from prompts import PROMPT_PLANNING, PROMPT_EXECUTION, PROMPT_FINAL
from helper_funtions import ( get_embeddings, build_faiss_index, search_chunks, ask_llm_for_json, ask_llm_for_text)


# This will make the task plan from the user goal (It will include/geerate 3-5 tasks based on the prompt)
def make_plan(goal, chunks):
    preview_lines = []

    for chunk in chunks[:4]:
        short_text = chunk["text"][:220]
        preview_lines.append(
            f'Chunk {chunk["id"]} (Page {chunk["page"]}): {short_text}'
        )

    preview = "\n".join(preview_lines)

    user_prompt = f"""
Goal:
{goal}

Document preview:
{preview}

Create 3 to 5 tasks.
Return JSON only.
"""

    data = ask_llm_for_json(PROMPT_PLANNING, user_prompt)
    tasks = data["tasks"]

    for i, task in enumerate(tasks, start=1):
        task["id"] = task.get("id", i)
        task["title"] = task.get("title", f"Task {i}")
        task["description"] = task.get("description", "")
        task["status"] = "pending"

    return tasks


# Prepare embeddings, search index, and tasks
def initializing_agent(goal, chunks):
    chunk_texts = [chunk["text"] for chunk in chunks]
    embeddings = get_embeddings(chunk_texts)
    index = build_faiss_index(embeddings)
    tasks = make_plan(goal, chunks)

    return tasks, index


# Run one task
def run_single_task(task, goal, chunks, index, completed_summaries):
    query = f'{goal}\nTask: {task["title"]}\nDescription: {task["description"]}'
    retrieved_chunks = search_chunks(query, chunks, index, top_k=4)

    chunk_text_block = []
    evidence_ids = []

    for chunk in retrieved_chunks:
        evidence_ids.append(chunk["id"])
        chunk_text_block.append(
            f'[Chunk {chunk["id"]} | Page {chunk["page"]}]\n{chunk["text"]}'
        )

    completed_text = "\n".join(completed_summaries) if completed_summaries else "None"

    user_prompt = f"""
User goal:
{goal}

Current task:
ID: {task["id"]}
Title: {task["title"]}
Description: {task["description"]}

Completed task summaries:
{completed_text}

Retrieved chunks:
{chr(10).join(chunk_text_block)}

Return JSON only.
"""

    result_data = ask_llm_for_json(PROMPT_EXECUTION, user_prompt)

    task["result"] = result_data.get("result", "")
    task["evidence_chunk_ids"] = result_data.get("evidence_chunk_ids", evidence_ids)
    task["status"] = "done" if task["result"] else "failed"


# Generate the final answer from finished tasks from the planner
def generate_final_answer(goal, tasks):
    task_texts = []

    for task in tasks:
        text = (
            f'Task {task["id"]}: {task["title"]}\n'
            f'Status: {task["status"]}\n'
            f'Result: {task.get("result", "")}'
        )
        task_texts.append(text)

    task_results_text = "\n\n".join(task_texts)

    final_prompt = f"""
Goal:
{goal}

Task results:
{task_results_text}
"""

    return ask_llm_for_text(PROMPT_FINAL, final_prompt)