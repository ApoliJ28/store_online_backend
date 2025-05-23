from pydantic import BaseModel, Field

class UserVerification(BaseModel):
    password: str
    new_password: str = Field(min_length= 6)
    
    class Config:
        json_schema_extra={
            "example":{
                "password":"password",
                "new_password":"new password"
            }
        }
