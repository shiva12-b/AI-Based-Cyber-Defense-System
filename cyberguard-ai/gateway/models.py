from typing import Optional, Literal
from pydantic import BaseModel, Field
class AccountCreate(BaseModel):
    name:str=Field(min_length=2,max_length=100); role:Literal['employee','customer']='employee'; initial_balance:float=Field(ge=0,le=100000000); password:str=Field(min_length=6,max_length=128)
class BeneficiaryCreate(BaseModel): owner_user_id:str; beneficiary_account_id:str; nickname:Optional[str]=None
class LoginIn(BaseModel): user_id:str; password:str; device_id:str
class TransferIn(BaseModel): user_id:str; session_id:str; to_account:str; amount:float=Field(gt=0,le=100000000); note:Optional[str]=Field(default='',max_length=200)
class AttackIn(BaseModel): user_id:str; session_id:str; scenario:Literal['credential_compromise','account_takeover','transaction_fraud','session_anomaly']
class HumanDecision(BaseModel): decision:Literal['ALLOW','BLOCK','KEEP_ISOLATED']
