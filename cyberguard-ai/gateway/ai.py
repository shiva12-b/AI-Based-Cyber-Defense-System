import json,httpx
from .config import env

def fallback(e,score,level,inds):
    if not inds: cls='legitimate'; rec='allow'; conf=96; summary='No material security indicators were observed.'
    elif score>=70: cls='possible_credential_compromise'; rec='isolate'; conf=min(98,65+score//4); summary='Multiple observed indicators are consistent with a possible compromised employee session.'
    else: cls='suspicious_activity'; rec='human_verification'; conf=68; summary='The request contains anomalous evidence but the available evidence is not sufficient for a definitive malicious classification.'
    return {'classification':cls,'confidence':conf,'severity':level.lower(),'recommended_action':rec,'summary':summary,'reasoning':'This assessment is derived only from the observed evidence supplied to the analyst. No unobserved user, device, malware or attack facts were assumed.','evidence':[i['evidence'] for i in inds],'investigation_steps':['Review the observed authentication and device context','Compare transaction context with observed account history','Verify the session with the employee or security operator'],'uncertainty':[] if score>=70 else ['The available telemetry does not prove attacker identity.']}
async def analyze(e,score,level,inds):
    key=env('GENAI_API_KEY')
    base=env('GENAI_BASE_URL').rstrip('/'); model=env('GENAI_MODEL','gemini-2.5-flash')
    if not key: return 'fallback',fallback(e,score,level,inds), 'GENAI_API_KEY is not configured'
    prompt={'observed_evidence':e,'deterministic_risk':{'score':score,'level':level,'indicators':inds},'required_output':['classification','confidence','severity','recommended_action','summary','reasoning','evidence','investigation_steps','uncertainty'],'rule':'Use only supplied evidence; never invent facts. Separate observed evidence from interpretation. If evidence is insufficient, say uncertain. Do not provide hidden chain-of-thought.'}
    try:
        if env('GENAI_PROVIDER','gemini').lower()=='gemini':
            url=f'{base}/models/{model}:generateContent?key={key}'; body={'system_instruction':{'parts':[{'text':'You are a security analyst. Return JSON only. Use only observed evidence.'}]},'contents':[{'parts':[{'text':json.dumps(prompt)}]}],'generationConfig':{'responseMimeType':'application/json'}}
            async with httpx.AsyncClient(timeout=20) as c: r=await c.post(url,json=body); r.raise_for_status(); data=r.json(); text=data['candidates'][0]['content']['parts'][0]['text']; return 'genai',json.loads(text),None
        return 'fallback',fallback(e,score,level,inds),'Unsupported GENAI_PROVIDER'
    except Exception as ex: return 'fallback',fallback(e,score,level,inds),f'GenAI fallback: {type(ex).__name__}'
