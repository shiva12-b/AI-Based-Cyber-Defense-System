def assess(e):
    inds=[]
    def add(k,w,why): inds.append({'id':k,'weight':w,'evidence':why})
    if e.get('unknown_device'): add('UNKNOWN_DEVICE',22,'Device is not trusted for this user.')
    if e.get('failed_auths',0)>=3: add('AUTH_ANOMALY',20,f"{e['failed_auths']} failed authentication attempts were observed recently.")
    if e.get('new_session'): add('NEW_SESSION',10,'A new session was created.')
    if e.get('new_beneficiary'): add('NEW_BENEFICIARY',16,'The transfer targets a beneficiary not previously used by this account.')
    if e.get('amount_deviation'): add('AMOUNT_DEVIATION',18,'The amount is materially outside the account holder\'s observed transaction range.')
    if e.get('rapid_activity'): add('RAPID_ACTIVITY',14,f"{e.get('recent_requests',0)} recent security-relevant requests were observed in the rolling window.")
    if e.get('session_device_mismatch'): add('SESSION_DEVICE_MISMATCH',24,'The active session is being used from an unexpected device context.')
    if e.get('sensitive_operation'): add('SENSITIVE_OPERATION',8,'The request attempts a financial operation requiring elevated trust.')
    score=min(100,sum(i['weight'] for i in inds)); level='LOW' if score<30 else 'MEDIUM' if score<70 else 'HIGH'; return score,level,inds
