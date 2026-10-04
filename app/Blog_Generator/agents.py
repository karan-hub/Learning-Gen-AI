import os 
from langchain_google_genai  import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from prompts import RESEARCHER_SYSTEM_PROMPT , WRITER_SYSTEM_PROMPT ,EDITOR_SYSTEM_PROMPT  


def get_model(model_name: str= "gemini-2.5-flash" , temp:  float = 0.5):
    api_key = os.getenv("GOOGLE_API_KEY")
    llm = ChatGoogleGenerativeAI(model= model_name , temperature= temp , api_key= api_key ,max_tokens=8192,)
    return llm


RESEARCHER_PROMPT = ChatPromptTemplate.from_messages([
    {
        "role": "system",
        "content": RESEARCHER_SYSTEM_PROMPT
    },
    {
        "role": "user",
        "content": """
topic: {topic}

audience: {target_audience}

revision_hits:
{revision_hits}
"""
    }
])

def researcher_agent(llm:ChatGoogleGenerativeAI , topic :str , audience : str , feedback: str ="") -> str:
    revision_hits = f" The humman provided this feedback on your previous reaserch -  please address it : { feedback}"
    if not feedback :
       revision_hits = "This is you first attempt"
    chain = RESEARCHER_PROMPT | llm

    result = chain.invoke({
        "topic" : topic ,
        "target_audience" :  audience,
        "revision_hits" : revision_hits
    })
 
    print("topic:", repr(topic))
    print("model response:", repr(result))
    print("response content:", repr(result.content))
    print("finish reason:", result.response_metadata.get("finish_reason"))
    print("usage:", result.usage_metadata)
    print("content:", repr(result.content))
    return result.content


WRITER_PROMPT= ChatPromptTemplate.from_messages([
    {"role" :"system" , "content": WRITER_SYSTEM_PROMPT} ,
    {"role": "user" , "content": "Topic: {topic} , Audience :{audience} , Reasearch Notes : {reaserch} , revision_hits:{revision_hits}" }
])



def writer_agent(llm:ChatGoogleGenerativeAI , topic :str , audience : str , feedback: str ="" , reaserch : str =" ") -> str:
    revision_hits = f" The humman provided this feedback on your previous draft and asked for there changes : { feedback} please apply there chagnes during writting blog "
    if not feedback :
       revision_hits = "This is you first attempt"
    chain = WRITER_PROMPT | llm

    result = chain.invoke({
        "topic" : topic ,
        "reaserch" :  reaserch,
        "audience" :audience,
        "revision_hits" : revision_hits
    })

    return result.content



EDITOR_PROMPT= ChatPromptTemplate.from_messages([
    {"role" :"system" , "content": EDITOR_SYSTEM_PROMPT} ,
    {"role": "user" , "content": "Topic: {topic} , draft :{draft}  return the puclished blog "}
])


def editor_agent(llm:ChatGoogleGenerativeAI , topic :str ,  draft : str) -> str:
 
    chain = EDITOR_PROMPT | llm

    result = chain.invoke({
        "topic" : topic ,
        "draft": draft
    })

    return result.content




