

import asyncio
import os
import json
from dotenv import load_dotenv
from workflows import Workflow, step, Context
from workflows.events import StartEvent, StopEvent
from openai import OpenAI
from individual_functions import (
    Content_grader,
    Content_writer,
    Content_changes_proposer,
    Content_refiner
)
from pydantic import BaseModel, Field

# -------------------------
# Load environment variables
# -------------------------
print("[INIT] Loading environment variables...")
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
assert OPENAI_API_KEY, "OPENAI_API_KEY not found"
print("[INIT] Environment variables loaded successfully")

client = OpenAI(api_key=OPENAI_API_KEY)
print("[INIT] OpenAI client initialized")

# -------------------------
# FINAL COMBINED PROMPT
# -------------------------
FINAL_EDITORIAL_REVIEW_AND_REFINEMENT_PROMPT = """
You are a Chief Editorial Officer overseeing publication-quality technical articles.

You must perform the following steps internally and sequentially:

STEP 1 — STRICT EVALUATION
Critically evaluate the given article using professional editorial standards.

Evaluate on:
1. Clarity and coherence
2. Structure and logical flow
3. Depth and completeness
4. Readability and engagement
5. SEO and discoverability best practices
6. Strength of introduction and conclusion
7. Overall editorial polish

Rules for scoring:
- Be strict and objective.
- Do NOT be lenient.
- Scores above 9.5 are rare and reserved for near-publishable content.
- Base the score solely on the content provided.

STEP 2 — DECISION
- If the score is GREATER THAN OR EQUAL TO the threshold, return the article unchanged.
- If the score is BELOW the threshold, improve the article to exceed the threshold.

STEP 3 — REFINEMENT (only if needed)
If improvement is required:
- Apply only high-impact, necessary changes.
- Preserve the original intent, tone, and structure.
- Improve clarity, flow, depth, engagement, and polish.
- Do NOT add unnecessary content.
- Do NOT explain or comment on changes.
- Do NOT include any notes or metadata.

CRITICAL OUTPUT RULES:
- Respond ONLY in valid JSON.
- Do NOT include markdown.
- Do NOT include explanations.
- Do NOT include analysis.
- The refined article must be publication-ready.


"""

class Output(BaseModel):
    score: int
    final_article: str

class Writer(BaseModel):
    output: str


# -------------------------
# Review + Refinement Function
# -------------------------
async def review_and_refine_article(article_content: str, threshold: float = 8):
    print("\n[REVIEW] Entered review_and_refine_article()")
    print(f"[REVIEW] Threshold set to: {threshold}")
    print("[REVIEW] Sending article to OpenAI for evaluation & refinement...")

    completion = client.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": FINAL_EDITORIAL_REVIEW_AND_REFINEMENT_PROMPT},
            {"role": "user", "content": article_content + f" threshold_value is : {threshold}"},
        ],
        response_format=Output,
    )

    print("[REVIEW] OpenAI response received")

    answer = completion.choices[0].message.parsed

    print(f"[REVIEW] Score received: {answer.score}")
    print("[REVIEW] Refinement completed successfully")

    return answer.score, answer.final_article


# -------------------------
# Workflow Definition
# -------------------------
class MainWorkflow(Workflow):

    @step
    async def start(self, ctx: Context, ev: StartEvent) -> StopEvent:
        print("\n[WORKFLOW] Workflow started")
        query = ev.input_msg
        print(f"[WORKFLOW] Input query received: {query}")

        MAX_REFINEMENTS = 3
        THRESHOLD = 8

        print("[WORKFLOW] Generating initial article...")
        article = await Content_writer(query=query)
        print("[WORKFLOW] Initial article generated")

        best_article = article
        best_score = 0.0

        print(f"[WORKFLOW] Starting refinement loop (max {MAX_REFINEMENTS} iterations)")

        for iteration in range(MAX_REFINEMENTS):
            print(f"\n[WORKFLOW] Refinement iteration {iteration + 1}")

            score, article = await review_and_refine_article(
                article_content=article,
                threshold=THRESHOLD
            )

            print(f"[WORKFLOW] Iteration {iteration + 1} score: {score}")

            if score > best_score:
                best_score = score
                best_article = article
                print("[WORKFLOW] Best article updated")

            if score >= THRESHOLD:
                print("[WORKFLOW] Threshold met. Running final grading...")

                score, justification, weaknesses = await Content_grader(article)

                print("**************************************************")
                print("[WORKFLOW] one more evaluation after finding the best article ,  Final Grader Score:", score)
                print("**************************************************")

                print("[WORKFLOW] Early exit from workflow")
                return StopEvent(result=article)

        print("[WORKFLOW] Threshold not met. Returning best available article")
        return StopEvent(result=best_article)


# -------------------------
# Runner
# -------------------------
async def main():
    print("\n[MAIN] Starting application...")

    workflow = MainWorkflow()

    result = await workflow.run(
        input_msg="Write an article on Retrieval Augmented Generation (RAG)"
    )

    print("\n===== GENERATED ARTICLE =====\n")
    print(result)

    print("\n[MAIN] Application finished successfully")


if __name__ == "__main__":
    asyncio.run(main())
