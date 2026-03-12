import streamlit as st

from agent import initializing_agent, run_single_task, generate_final_answer
from helper_funtions import save_uploaded_file, load_pdf, OPENAI_API_KEY

st.set_page_config(page_title="Document Helper Agent", layout="wide")

# To show all tasks on the left side in Stremlit for debugging purposes. Otherwise, it is not required to show on the UI
def show_tasks(task_box, tasks):
    with task_box.container():
        st.subheader("Task Board")

        for task in tasks:
            with st.container(border=True):
                st.markdown(f'**Task {task["id"]}: {task["title"]}**')
                st.write(task["description"])
                st.write(f'Status: `{task["status"]}`')

                if task.get("result"):
                    st.markdown("**Result**")
                    st.write(task["result"])

                if task.get("evidence_chunk_ids"):
                    st.write(f'Evidence chunks: {task["evidence_chunk_ids"]}')


# Show progress messages on the right side in streamlit
def show_progress(progress_box, messages):
    with progress_box.container(border=True):
        st.subheader("Progress")
        for msg in messages:
            st.write(msg)


# Main app which will trigger all other functions
def main():
    st.title("Document Helper Agent")

    with st.sidebar:
        uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
        goal = st.text_area(
            "Write your goal:",
            placeholder="Example: Summarize this document and identify risks.",
            height=140
        )
        run_button = st.button("Run Agent", type="primary")

    st.write("Upload a PDF and give the agent a goal.")

    if not run_button:
        return

    #Few checks before setting up the Agent
    if not OPENAI_API_KEY:
        st.error("OPENAI_API_KEY is missing.")
        return

    if not uploaded_file:
        st.error("Please upload a PDF.")
        return

    if not goal.strip():
        st.error("Please enter a goal.")
        return

    try:
        with st.spinner("Saving file.."):
            file_path = save_uploaded_file(uploaded_file)

        with st.spinner("Reading PDF.."):
            chunks = load_pdf(file_path)

        st.success(f"Loaded {len(chunks)} chunks.")

        with st.spinner("Preparing agent (Embeddings, Faiss index etc).. (for debugging)"):
            tasks, index = initializing_agent(goal, chunks)

        left, right = st.columns([1, 1])

        with left:
            task_box = st.empty()
            final_box = st.empty()

        with right:
            progress_box = st.empty()

        show_tasks(task_box, tasks)

        completed_summaries = []
        progress_messages = []

        for task in tasks:
            progress_messages.append(f'Running task {task["id"]}: {task["title"]}')
            show_progress(progress_box, progress_messages)

            task["status"] = "in_progress"
            show_tasks(task_box, tasks)

            run_single_task(task, goal, chunks, index, completed_summaries)

            completed_summaries.append(
                f'Task {task["id"]} - {task["title"]}: {task.get("result", "")}'
            )

            progress_messages.append(f'Completed task {task["id"]}: {task["title"]}')
            show_progress(progress_box, progress_messages)

            show_tasks(task_box, tasks)

        progress_messages.append("Writing final answer..")
        show_progress(progress_box, progress_messages)

        final_answer = generate_final_answer(goal, tasks)

        with final_box.container(border=True):
            st.subheader("Final Answer")
            st.write(final_answer)

        progress_messages.append("All tasks completed.")
        show_progress(progress_box, progress_messages)

    except Exception as e:
        st.exception(e)


if __name__ == "__main__":
    main()