# Document Helper Agent

A small AI agent that helps a user work through a document-based goal.

The user uploads a PDF and gives a high-level goal such as:
- summarize the paper
- extract main ideas

## Note:
- **Demo Video is included in the project folder**
- **PDF file (Test_doc_artificial_intelligence.pdf) which is used for this test is inlcuded in the project folder.**
- A sample run is included in `example_transcript.md`, and a screenshot of the output is included in `example_transcript.png` in the project folder.

## How the agent works

**PDF upload → task plan → retrieval → execution → final answer**

A simple RAG flow:

1. The user uploads a PDF and writes what they want the system to do.
2. The PDF is read and split into smaller chunks.
3. Embeddings are created for those chunks.
4. A FAISS index is built so the system can retrieve relevant parts of the document.
5. The model creates a short plan from the user goal, usually 3 to 5 tasks.
6. The tasks are then executed one at a time. For each task, the system:
   - selects the current task
   - retrieves the 4 most relevant chunks from the document
   - sends the task, the retrieved chunks, and short notes from completed tasks to the model
   - saves the result
   - updates the task status
7. After all tasks are done, the system writes the final answer based on the task results.

## Tools used

This project uses real tools, not just a single API call.

- **PDF reading** with **pypdf**
- **Semantic retrieval** with embeddings + FAISS
- **OpenAI API** for planning, task execution, final answer, and embeddings

## Context strategy

One thing I wanted to avoid was sending the whole PDF to the model every time. That would make the prompt unnecessarily large and less focused.

Instead, I split the document into chunks, create embeddings once, and use FAISS retrieval during execution. For each task, I only send:
- the user goal
- the current task
- short notes from already completed tasks
- the 4 most relevant chunks for that task

Using only 4 retrieved chunks keeps the context small enough to stay focused, while still giving the model enough evidence to work with. This was a simple trade-off between keeping prompts short and still grounding the answer in the document.

## Features

This prototype includes:
- a minimal Streamlit UI
- a small RAG-style setup over the uploaded PDF
- simple progress logs
- basic evidence display in the task board

## Trade-offs

I simplified a few things on purpose:
- PDF only
- one document at a time
- local FAISS instead of an external vector database
- simple progress logging
- no persistence / resume

I chose these trade-offs to keep the project small and polished.

## Setup

### 1. Create and activate environment

```bash
conda create -n doc-helper python=3.11
conda activate doc-helper
```

### 2. Install FAISS

```bash
conda install -c conda-forge faiss-cpu
```
### 3. Install the remaining packages

```bash
pip install -r requirements.txt
```

### 4. Add environment variables

- Create a .env file based on .env.example file.

### 5. Run the app

```bash
streamlit run app.py
```

## Evaluation scenarios

I would test the system with a few simple cases like these:

### 1. Document summary
**Goal:** Summarize the paper and extract its main ideas  
**What success looks like:** The task outputs stay on topic, and the final answer clearly reflects the actual content of the paper

### 2. Focused question over a longer PDF
**Goal:** Answer one specific question from a longer technical document  
**What success looks like:** The system retrieves the relevant parts of the document for that question instead of depending on the whole PDF as context

### 3. Methods and applications
**Goal:** Identify the main techniques discussed in the paper and where they are applied  
**What success looks like:** The retrieved chunks are relevant, and the final answer clearly separates the methods from their practical uses

# What I would improve next

If I extended the project, I would add:

- OCR support for scanned PDFs

- persistence / resume support

- multi-document retrieval