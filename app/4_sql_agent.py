from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_community.utilities  import SQLDatabase
from langchain_community.agent_toolkits  import SQLDatabaseToolkit
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent
import streamlit as st

db = SQLDatabase.from_uri("sqlite:///my_tasks.db")

db.run("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT CHECK (status IN ('pending', 'in_progress', 'completed')) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
       );
""")

model = ChatGroq(model="openai/gpt-oss-20b", streaming=True)
toolkit= SQLDatabaseToolkit(db=db, llm=model)
tools=toolkit.get_tools()

system_prompt = """
You are a task management assistant that interacts with a SQL database containing a 'tasks' table. 

TASK RULES:
1. Limit SELECT queries to 10 results max with ORDER BY created_at DESC
2. After CREATE/UPDATE/DELETE, confirm with SELECT query
3. If the user requests a list of tasks, present the output in a structured table format to ensure a clean and organized display in the browser."

CRUD OPERATIONS:
    CREATE: INSERT INTO tasks(title, description, status)
    READ: SELECT * FROM tasks WHERE ... LIMIT 10
    UPDATE: UPDATE tasks SET status=? WHERE id=? OR title=?
    DELETE: DELETE FROM tasks WHERE id=? OR title=?

Table schema: id, title, description, status(pending/in_progress/completed), created_at.
"""


def get_agent():
    return create_agent(
        model=model,
        tools=tools,
        checkpointer=InMemorySaver(),
        system_prompt= system_prompt,
    )

agent=get_agent()


st.subheader("📜 TaskBot - Manage Your Tasks")

if "messages" not in  st.session_state:
    st.session_state.messages=[]

for message in st.session_state.messages:
    st.chat_message(message["role"]).markdown(message["content"])


user_message= st.chat_input("Ask me to manage your tasks ?")

if user_message:
    st.chat_message("user").markdown(user_message)
    st.session_state.messages.append({"role":"user", "content":user_message})

    with st.chat_message("ai"):
        with  st.spinner("Processing..."):
            responce= agent.stream(
                  {"messages":[{"role":"user", "content":user_message}]},
                  {"configurable":{"thread_id":"1"}},
                  stream_mode="messages"
            )

            space= st.empty()
            message =" "
            for chuck in responce:
                message += chuck[0].content
                space.write(message)

            st.session_state.messages.append({"role":"ai", "content":message})
