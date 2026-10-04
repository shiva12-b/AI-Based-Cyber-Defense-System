from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from . import db
from datetime import datetime, timezone
import uuid, os, hashlib
SECRET=os.getenv('PROTECTED_SHARED_SECRET','change-this-local-secret')
app=FastAPI(title='CyberBank Synthetic Server')
class AccountIn(BaseModel): user_id:str; name:str; role:str='employee'; initial_balance:float=Field(ge=0); password:str
class BeneficiaryIn(BaseModel): owner_user_id:str; beneficiary_account_id:str; nickname:str|None=None
class TransferIn(BaseModel): from_account:str; to_account:str; amount:float=Field(gt=0); request_id:str; reason:str|None=None

def auth(s):
    if s!=SECRET: raise HTTPException(403,'Bank server accepts application traffic only through CyberGuard')
@app.on_event('startup')
def startup(): db.init()
@app.get('/health')
def health(): return {'ok':True,'service':'synthetic-bank-server'}
@app.post('/internal/accounts')
def create_account(x:AccountIn,x_cyberguard_secret:str=Header(default='')):
    auth(x_cyberguard_secret); uid=x.user_id or 'USR-'+uuid.uuid4().hex[:8]; db.execute('INSERT INTO users VALUES(?,?,?,?,?)',(uid,x.name,x.role,hashlib.sha256(x.password.encode()).hexdigest(),db.now())); aid='ACC-'+uuid.uuid4().hex[:8].upper(); db.execute('INSERT INTO accounts VALUES(?,?,?,?,?,?)',(aid,uid,'****'+aid[-4:],x.initial_balance,'ACTIVE',db.now())); return {'user_id':uid,'account_id':aid,'account_no':'****'+aid[-4:],'balance':x.initial_balance}
@app.post('/internal/login')
def internal_login(x:dict,x_cyberguard_secret:str=Header(default='')):
    auth(x_cyberguard_secret); u=db.one('SELECT * FROM users WHERE id=?',(x.get('user_id'),))
    if not u or u['password_hash']!=hashlib.sha256(str(x.get('password','')).encode()).hexdigest(): raise HTTPException(401,'Invalid employee credentials')
    return {'id':u['id'],'name':u['name'],'role':u['role']}

@app.get('/internal/accounts')
def accounts(x_cyberguard_secret:str=Header(default='')):
    auth(x_cyberguard_secret); return db.rows('SELECT a.*,u.name,u.role FROM accounts a JOIN users u ON u.id=a.user_id ORDER BY a.created_at DESC')
@app.get('/internal/accounts/{user_id}')
def account(user_id:str,x_cyberguard_secret:str=Header(default='')):
    auth(x_cyberguard_secret); r=db.one('SELECT a.*,u.name,u.role FROM accounts a JOIN users u ON u.id=a.user_id WHERE u.id=?',(user_id,));
    if not r: raise HTTPException(404,'Account not found')
    return r
@app.post('/internal/beneficiaries')
def beneficiary(x:BeneficiaryIn,x_cyberguard_secret:str=Header(default='')):
    auth(x_cyberguard_secret); bid='BEN-'+uuid.uuid4().hex[:8].upper(); db.execute('INSERT INTO beneficiaries VALUES(?,?,?,?,?)',(bid,x.owner_user_id,x.beneficiary_account_id,x.nickname,db.now())); return {'id':bid}
@app.get('/internal/beneficiaries/{user_id}')
def beneficiaries(user_id:str,x_cyberguard_secret:str=Header(default='')):
    auth(x_cyberguard_secret); return db.rows('SELECT b.*,a.account_no,u.name FROM beneficiaries b JOIN accounts a ON a.id=b.beneficiary_account_id JOIN users u ON u.id=a.user_id WHERE b.owner_user_id=?',(user_id,))
@app.post('/internal/transfer')
def transfer(x:TransferIn,x_cyberguard_secret:str=Header(default='')):
    auth(x_cyberguard_secret); c=db.conn(); c.execute('BEGIN IMMEDIATE'); src=c.execute('SELECT * FROM accounts WHERE id=?',(x.from_account,)).fetchone(); dst=c.execute('SELECT * FROM accounts WHERE id=?',(x.to_account,)).fetchone()
    if not src or not dst: c.rollback(); raise HTTPException(404,'Account not found')
    if src['balance']<x.amount: c.rollback(); raise HTTPException(400,'Insufficient funds')
    c.execute('UPDATE accounts SET balance=balance-? WHERE id=?',(x.amount,x.from_account)); c.execute('UPDATE accounts SET balance=balance+? WHERE id=?',(x.amount,x.to_account)); tid='TXN-'+uuid.uuid4().hex[:10].upper(); c.execute('INSERT INTO transactions VALUES(?,?,?,?,?,?,?,?)',(tid,db.now(),x.from_account,x.to_account,x.amount,'SUCCESS',x.reason,x.request_id)); c.commit(); c.close(); return {'transaction_id':tid,'status':'SUCCESS','amount':x.amount}
@app.get('/internal/transactions/{user_id}')
def txns(user_id:str,x_cyberguard_secret:str=Header(default='')):
    auth(x_cyberguard_secret); return db.rows('SELECT t.*,a.user_id FROM transactions t JOIN accounts a ON a.id=t.from_account WHERE a.user_id=? ORDER BY t.ts DESC',(user_id,))
