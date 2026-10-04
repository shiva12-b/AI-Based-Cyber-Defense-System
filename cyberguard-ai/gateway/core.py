from .db import one,rows,execute,now,j
from .risk import assess
from .ai import analyze
import uuid

def history(user_id,device_id):
    recent=one("SELECT COUNT(*) c FROM events WHERE user_id=? AND ts>=datetime('now','-10 minutes')",(user_id,))['c']
    failed=one("SELECT COUNT(*) c FROM events WHERE user_id=? AND type='AUTH_FAILURE' AND ts>=datetime('now','-10 minutes')",(user_id,))['c']
    prior=one("SELECT 1 x FROM transactions t JOIN accounts a ON a.id=t.from_account WHERE a.user_id=? AND t.status='SUCCESS' ORDER BY t.ts DESC LIMIT 1",(user_id,)) is not None
    trusted=one('SELECT trusted FROM devices WHERE id=? AND user_id=?',(device_id,user_id)); return {'recent_requests':recent,'failed_auths':failed,'prior_transactions':prior,'device_trusted':bool(trusted and trusted['trusted'])}

def transaction_context(user_id,device_id,session_id,to_account,amount):
    h=history(user_id,device_id); ben=one('SELECT 1 x FROM beneficiaries WHERE owner_user_id=? AND beneficiary_account_id=?',(user_id,to_account)) is not None
    avg=one("SELECT AVG(amount) a FROM transactions t JOIN accounts a ON a.id=t.from_account WHERE a.user_id=? AND t.status='SUCCESS'",(user_id,)); avg_amt=float(avg['a'] or 0); deviation=avg_amt>0 and amount>avg_amt*4
    sess=one('SELECT device_id FROM sessions WHERE id=? AND user_id=?',(session_id,user_id)); mismatch=bool(sess and sess['device_id']!=device_id)
    e={'unknown_device':not h['device_trusted'],'failed_auths':h['failed_auths'],'new_session':False,'new_beneficiary':not ben,'amount_deviation':deviation,'rapid_activity':h['recent_requests']>=8,'recent_requests':h['recent_requests'],'session_device_mismatch':mismatch,'sensitive_operation':True,'amount':amount,'average_amount':round(avg_amt,2),'to_account':to_account,'device_id':device_id,'session_id':session_id}
    return e
async def investigate(request_id,e,score,level,inds):
    status,res,err=await analyze(e,score,level,inds); iid='INC-'+uuid.uuid4().hex[:8].upper(); rec=res.get('recommended_action','human_verification');
    execute('INSERT INTO incidents VALUES(?,?,?,?,?,?,?,?,?,?,?)',(iid,request_id,now(),'ACTIVE',res.get('classification'),score,res.get('confidence'),res.get('summary'),rec,j(res.get('evidence',[])),j(res)))
    return iid,status,res,err
