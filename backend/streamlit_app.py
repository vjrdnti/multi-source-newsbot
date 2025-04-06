import streamlit as st
import requests

API_URL_SUMMARIZE_INDIVIDUAL = "http://127.0.0.1:5000/summary_individual"
API_URL_SUMMARIZE_FINAL = "http://127.0.0.1:5000/final_summary"

st.set_page_config(page_title="News Summarizer", layout="wide")

st.title("📰 AI News Summarizer with Gemma")

query = st.text_input("Enter a news topic you'd like summarized:", "")

if st.button("Summarize") and query:
    with st.spinner("Fetching and summarizing articles..."):
        try:
            # Step 1: Call Flask summarize endpoint
            response = requests.post(API_URL_SUMMARIZE_INDIVIDUAL, json={"query": query})
            response.raise_for_status()
            summaries = response.json()

            if not summaries:
                st.warning("No relevant articles found.")
            else:
                st.subheader("🔍 Individual Summaries:")
                all_summary_texts = []
                for item in summaries:
                    st.markdown(f"**🗞️ Source:** [{item['source']}]({item['final_url']})")
                    st.markdown(item['summary'])
                    all_summary_texts.append(item['summary'])

                # Step 2: Generate final summary from all individual ones
                combined = "\n\n".join(all_summary_texts)
                st.divider()
                st.subheader("🧠 Final Combined Summary:")

                final_summary = "No final summary."
                if combined:
                    response2 = requests.post(API_URL_SUMMARIZE_FINAL)
                    result = response2.json()
                    final_summary = result.get("summary", "")

                st.markdown(final_summary)

        except Exception as e:
            st.error(f"Error: {e}")
