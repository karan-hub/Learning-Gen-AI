from pydantic import BaseModel 

class BlogState(BaseModel):
    # user Input
    topic : str = ""
    audience :  str= "Genaral"

    # Researcher Output
    research :  str =""
    research_feedback:  str =""


    # Writer Output
    draft :  str =""
    draft_feedback:  str =""

    # editor Output
    final_blog: str= ""


    # meta data
    revision_count:int = 0
    