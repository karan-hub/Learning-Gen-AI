from langgraph.graph import StateGraph  , START , END
from langgraph.checkpoint.memory  import InMemorySaver
from langgraph.types import interrupt , Command
from agents import get_model
from state import BlogState
from agents import researcher_agent , writer_agent , editor_agent
from typing import  Literal

from prompts import( RESEARCHER_NODE_DOC_STR , 
                     WRITER_NODE_DOC_STR , 
                    EDITOR_NODE_DOC_STR ,
                    HUMMAN_REVIEW_RESEARCH_NODE_DOC_STR ,
                    HUMMAN_REVIEW_WRITER_NODE_DOC_STR)

MAX_REVISION= 3

def researcher_node(state: BlogState) -> BlogState:
    f"{RESEARCHER_NODE_DOC_STR}"
    llm = get_model()
 
    research_data = researcher_agent(
        llm=llm,
        topic= state.topic,
        audience= state.audience,
        feedback= state.research_feedback
    )
    print("research_data ",research_data )
    state.research = research_data
    state.research_feedback = "" 

    return state


def humman_review_research_node(state: BlogState):
    decision = interrupt({
        "stage": "research_review",
        "research": state.research,
        "instruction": (
            "Reply with approve to continue back to the research agent "
            "or describe what changes needed"
        )
    })

    if isinstance(decision, dict):
        action = decision.get("action", "Approve").lower()
        feedback = decision.get("feedback", "")
    else:
        text = str(decision)
        action = "approve" if text.lower() in ["approve", "ok", "process"] else "revise"
        feedback = "" if action == "approve" else text

    if action == "revise" and feedback.strip():
        state.research_feedback = feedback
        state.revision_count += 1
    else:
        state.research_feedback = ""

    return state

def writer_node(state: BlogState) -> BlogState:
    f"{WRITER_NODE_DOC_STR}"
    
    llm = get_model()
    
    draft_data = writer_agent(
            llm=llm,
            topic= state.topic,
            reaserch= state.research,
            audience= state.audience,
            feedback= state.draft_feedback
        )
    state.draft = draft_data
    state.draft_feedback =""

    return state

def humman_review_writer_node(state: BlogState):
    decision = interrupt({
        "state": "draft_review",
        "draft": state.draft,
        "instruction": (
            "Reply with approve to continue to the editor "
            "or describe what changes needed"
        )
    })

    if isinstance(decision, dict):
        action = decision.get("action", "Approve").lower()
        feedback = decision.get("feedback", "")
    else:
        text = str(decision)
        action = "approve" if text.lower() in ["approve", "ok", "process"] else "revise"
        feedback = "" if action == "approve" else text

    if action == "revise" and feedback.strip():
        state.draft_feedback = feedback
        state.revision_count += 1
    else:
        state.draft_feedback = ""

    return state

def editor_node(state: BlogState) -> BlogState :
    f"{EDITOR_NODE_DOC_STR}"
    llm= get_model()
    final = editor_agent(
        llm= llm,
        topic= state.topic,
        draft = state.draft
    )

    state.final_blog = final
    return state


def route_after_research_review(state: BlogState):
    return "research" if state.research_feedback else "writer"

def route_after_draft_review(state: BlogState):
    return "writer" if state.draft_feedback and state.revision_count < MAX_REVISION else "edit"



def build_blog_graph():
    builder=  StateGraph(BlogState)
    builder.add_node("research" , researcher_node)
    builder.add_node("review_research" , humman_review_research_node)
    builder.add_node("writer" , writer_node)
    builder.add_node("reviwe_draft" , humman_review_writer_node)
    builder.add_node("edit" , editor_node)

    builder.add_edge(START , "research")
    builder.add_edge("research" , "review_research")
    builder.add_conditional_edges("review_research" , route_after_research_review , {"research":"research" , "writer":"writer"} )
    builder.add_edge("writer" ,"reviwe_draft")
    builder.add_conditional_edges("reviwe_draft" , route_after_draft_review , { "writer":"writer" , "edit" :"edit"} )
    builder.add_edge("edit" , END)

    GRAPH=  builder.compile(checkpointer=InMemorySaver())
    return GRAPH

