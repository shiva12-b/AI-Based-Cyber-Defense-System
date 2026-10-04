from gateway.risk import assess

def test_low_risk():
 s,l,i=assess({}); assert s==0 and l=='LOW'
def test_high_risk():
 s,l,i=assess({'unknown_device':True,'failed_auths':4,'new_beneficiary':True,'amount_deviation':True,'rapid_activity':True,'session_device_mismatch':True,'sensitive_operation':True,'recent_requests':12}); assert s>=70 and l=='HIGH'
