import streamlit as st
import os
from dotenv import load_dotenv
# Import your compiled agent pipeline directly from your agent file
from agent import build_graph 

load_dotenv()

st.set_page_config(page_title="AI Web Researcher", page_icon="🔍", layout="wide")
st.title("🔍 Advanced Web Research Agent")
st.write("Powered by LangGraph + Tavily Search + Google Gemini")

user_query = st.text_input("Enter your research topic:", placeholder="e.g., Quantum computing breakthroughs")

if st.button("Run Research Agent"):
    if not user_query.strip():
        st.warning("Please enter a topic.")
    else:
        with st.spinner("Agent is searching the web and synthesizing notes..."):
            try:
                # Compile and call your exact LangGraph logic
                agent = build_graph()
                result = agent.invoke({"query": user_query, "messages": [], "search_results": [], "report": ""})
                
                # Show output beautifully in a markdown card component
                st.success("Research Complete!")
                st.markdown("### 📄 Compiled Research Report")
                st.info(result["report"])
                
            except Exception as e:
                st.error(f"Execution Error: {e}")