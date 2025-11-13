from pydantic import BaseModel
from typing import Optional

class CustomerInquiryRequest(BaseModel):
    customer_inquiry: str

class CustomerInquiryResponse(BaseModel):
    original_inquiry: str
    category: str
    suggested_response: str