import uuid, json, httpx, os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .config import env,csv
from . import db
from .models import AccountCreate,BeneficiaryCreate,LoginIn,TransferIn,AttackIn,HumanDecision
from .core import transaction_context,investigate,history
from .risk import assess
app=FastAPI(title='CyberGuard AI')
app.add_middleware(CORSMiddleware,allow_origins=csv('CORS_ORIGINS','*'),allow_methods=['*'],allow_headers=['*'])
BANK=env('BANK_SERVER_URL','http://127.0.0.1:9000').rstrip('/'); SECRET=env('PROTECTED_SHARED_SECRET','change-this-local-secret')
@app.on_event('startup')
def startup(): db.init()
async def bank(method,path,**kwargs):
 async with httpx.AsyncClient(timeout=8) as c:
  r=await c.request(method,BANK+path,headers={'X-CyberGuard-Secret':SECRET},**kwargs)
  if r.status_code>=400: raise HTTPException(r.status_code,r.text)
  return r.json()
def event(uid,did,sid,typ,data): db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?)',( 'EV-'+uuid.uuid4().hex[:10].upper(),db.now(),uid,did,sid,typ,db.j(data)))
def audit(rid,event_name,detail): db.execute('INSERT INTO audit(ts,request_id,event,detail) VALUES(?,?,?,?)',(db.now(),rid,event_name,detail))
@app.get('/health')
def health(): return {'ok':True,'genai_configured':bool(env('GENAI_API_KEY')),'bank_url':BANK}
@app.get('/')
def home(): return FileResponse('frontend/index.html')
app.mount('/static',StaticFiles(directory='frontend'),name='static')
@app.get('/api/accounts')
async def accounts(): return await bank('GET','/internal/accounts')
@app.post('/api/accounts')
async def create_account(x:AccountCreate):
 uid='USR-'+uuid.uuid4().hex[:8].upper(); return await bank('POST','/internal/accounts',json={'user_id':uid,**x.model_dump()})
@app.post('/api/beneficiaries')
async def add_ben(x:BeneficiaryCreate): return await bank('POST','/internal/beneficiaries',json=x.model_dump())
@app.get('/api/beneficiaries/{uid}')
async def bens(uid): return await bank('GET',f'/internal/beneficiaries/{uid}')
@app.post('/api/login')
async def login(x:LoginIn):
 bank_user=await bank('POST','/internal/login',json={'user_id':x.user_id,'password':x.password})
 sid='SES-'+uuid.uuid4().hex[:10].upper(); ts=db.now(); known=db.one('SELECT * FROM devices WHERE id=? AND user_id=?',(x.device_id,x.user_id)); trusted=1 if (not known or known['trusted']) else 0
 if known: db.execute('UPDATE devices SET last_seen=? WHERE id=?',(ts,x.device_id))
 else: db.execute('INSERT INTO devices VALUES(?,?,?,?,?,?)',(x.device_id,x.user_id,x.device_id,1,ts,ts))
 db.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?)',(sid,x.user_id,x.device_id,ts,ts,'ACTIVE')); event(x.user_id,x.device_id,sid,'LOGIN_SUCCESS',{'device_known':bool(known)}); return {'session_id':sid,'device_trusted':bool(trusted),'user':bank_user}
@app.post('/api/auth-failure')
def auth_failure(x:LoginIn):
 event(x.user_id,x.device_id,None,'AUTH_FAILURE',{'source':'controlled_application_event'}); return {'recorded':True}
@app.get('/api/me/{uid}')
async def me(uid): return await bank('GET',f'/internal/accounts/{uid}')
@app.get('/api/transactions/{uid}')
async def transactions(uid): return await bank('GET',f'/internal/transactions/{uid}')
@app.post('/api/transfer')
async def transfer(x:TransferIn):
 req='REQ-'+uuid.uuid4().hex[:10].upper(); a=await bank('GET',f'/internal/accounts/{x.user_id}')
 if not a: raise HTTPException(404,'Source account not found')
 e=transaction_context(x.user_id, 'UNKNOWN', x.session_id,x.to_account,x.amount); s=one_session=x.session_id
 sess=db.one('SELECT * FROM sessions WHERE id=?',(s,)); did=sess['device_id'] if sess else 'UNKNOWN'; e=transaction_context(x.user_id,did,s,x.to_account,x.amount); score,level,inds=assess(e)
 if score>=30:
  iid,status,ai,err=await investigate(req,e,score,level,inds); rec=ai.get('recommended_action','human_verification')
 else: iid=None; status='not_required'; ai=None; err=None; rec='allow'
 decision='BLOCK' if score>=80 else 'ISOLATE' if score>=45 or rec in ('isolate','human_verification') else 'ALLOW'
 reason=ai.get('summary') if ai else 'No material security indicators were observed.'
 forwarded=False; bank_result=None
 if decision=='ALLOW':
  bank_result=await bank('POST','/internal/transfer',json={'from_account':a['id'],'to_account':x.to_account,'amount':x.amount,'request_id':req,'reason':'CyberGuard allowed'}); forwarded=True
  event(x.user_id,did,s,'TRANSACTION_ALLOWED',{'request_id':req,'amount':x.amount})
 else: event(x.user_id,did,s,'TRANSACTION_BLOCKED',{'request_id':req,'amount':x.amount,'decision':decision})
 db.execute('INSERT INTO requests VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(req,db.now(),x.user_id,did,s,x if False else 'POST','/api/transfer','TRANSFER',db.j({'to_account':x.to_account,'amount':x.amount}),score,level,decision,reason,int(forwarded),bank_result['status'] if bank_result else 'BLOCKED'))
 audit(req,'REQUEST_RECEIVED',f'Transfer ₹{x.amount:g} requested'); audit(req,'DECISION',f'{decision}: {reason}')
 return {'request_id':req,'decision':decision,'risk_score':score,'risk_level':level,'reason':reason,'incident_id':iid,'ai_status':status,'ai_report':ai,'forwarded':forwarded,'bank_result':bank_result}
@app.post('/api/attack')
async def attack(x:AttackIn):
 # Controlled simulation: creates actual application telemetry, then submits a real transfer request.
 dev='SIM-ATTACK-'+uuid.uuid4().hex[:6].upper(); attack_sid='SES-'+uuid.uuid4().hex[:10].upper(); ts=db.now()
 db.execute('INSERT INTO devices VALUES(?,?,?,?,?,?)',(dev,x.user_id,dev,0,ts,ts))
 db.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?)',(attack_sid,x.user_id,dev,ts,ts,'ACTIVE'))
 for _ in range(6): event(x.user_id,dev,attack_sid,'AUTH_FAILURE',{'simulation':x.scenario})
 event(x.user_id,dev,attack_sid,'SUSPICIOUS_ENDPOINT_ACTIVITY',{'simulation':x.scenario})
 accounts=await bank('GET','/internal/accounts'); target=[a for a in accounts if a['user_id']!=x.user_id]; src=next((a for a in accounts if a['user_id']==x.user_id),None)
 if not src or not target: raise HTTPException(400,'Create at least two accounts before running a controlled attack.')
 amount={'credential_compromise':min(src['balance'],40000),'account_takeover':min(src['balance'],60000),'transaction_fraud':min(src['balance'],50000),'session_anomaly':min(src['balance'],30000)}[x.scenario]
 if amount<=0: raise HTTPException(400,'Source account has no demo balance.')
 return await transfer(TransferIn(user_id=x.user_id,session_id=attack_sid,to_account=target[0]['id'],amount=amount,note='controlled security test'))
@app.get('/api/events')
def events(limit:int=100): return db.rows('SELECT * FROM events ORDER BY ts DESC LIMIT ?',(max(1,min(limit,500)),))
@app.get('/api/incidents')
def incidents(limit:int=100): return db.rows('SELECT * FROM incidents ORDER BY created_at DESC LIMIT ?',(max(1,min(limit,200)),))
@app.get('/api/incidents/{iid}')
def incident(iid):
 r=db.one('SELECT * FROM incidents WHERE id=?',(iid,));
 if not r: raise HTTPException(404,'Incident not found')
 for k in ('evidence','ai_report'): r[k]=json.loads(r[k] or '[]')
 req=db.one('SELECT * FROM requests WHERE id=?',(r['request_id'],)); return {'incident':r,'request':req,'audit':db.rows('SELECT * FROM audit WHERE request_id=? ORDER BY ts',(r['request_id'],))}
@app.get('/api/stats')
async def stats():
 a=await bank('GET','/internal/accounts')
 return {'accounts':len(a),'events':db.one('SELECT COUNT(*) c FROM events')['c'],'incidents':db.one('SELECT COUNT(*) c FROM incidents')['c'],'blocked':db.one("SELECT COUNT(*) c FROM requests WHERE decision='BLOCK'")['c'],'isolated':db.one("SELECT COUNT(*) c FROM requests WHERE decision='ISOLATE'")['c'],'allowed':db.one("SELECT COUNT(*) c FROM requests WHERE decision='ALLOW'")['c']}
@app.post('/api/decision/{rid}')
def human(rid,x:HumanDecision):
 r=db.one('SELECT * FROM requests WHERE id=?',(rid,));
 if not r: raise HTTPException(404,'Request not found')
 final='ISOLATE' if x.decision=='KEEP_ISOLATED' else x.decision; db.execute('UPDATE requests SET decision=?,reason=? WHERE id=?',(final,'Human security operator decision',rid)); audit(rid,'HUMAN_DECISION',final); return {'request_id':rid,'decision':final}
