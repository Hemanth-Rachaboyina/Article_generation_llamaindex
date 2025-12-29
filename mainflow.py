# import asyncio
# import os
# from dotenv import load_dotenv
# from workflows import Workflow, step, Context
# from workflows.events import StartEvent, StopEvent
# from openai import OpenAI
# from individual_functions import Content_grader,Content_writer, Content_changes_proposer, Content_refiner

# # -------------------------
# # Load environment variables
# # -------------------------
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# assert OPENAI_API_KEY, "OPENAI_API_KEY not found"

# client = OpenAI(api_key=OPENAI_API_KEY)

# # -------------------------
# # Content Writer Function
# # -------------------------



# # -------------------------
# # Workflow Definition
# class MainWorkflow(Workflow):

#     @step
#     async def start(self, ctx: Context, ev: StartEvent) -> StopEvent:
#         query = ev.input_msg

#         MAX_REFINEMENTS = 3
#         THRESHOLD = 9

#         # Step 1: initial article
#         article = await Content_writer(query=query)

#         best_article = article
#         best_score = 0

#         for attempt in range(MAX_REFINEMENTS):

#             score, justification, weaknesses = await Content_grader(
#                 article_content=article
#             )

#             # Track best version
#             if score > best_score:
#                 best_score = score
#                 best_article = article

#             # ✅ If quality is good enough, stop immediately
#             if score >= THRESHOLD:
#                 return StopEvent(result=article)

#             # ❌ Otherwise refine
#             changes = await Content_changes_proposer(
#                 article_content=article,
#                 score=score,
#                 justification=justification,
#                 weaknesses=weaknesses , Threshold=THRESHOLD
#             )

#             article = await Content_refiner(
#                 changes=changes,
#                 article_content=article
#             )

#         # If max attempts reached, return best attempt
#         return StopEvent(result=best_article)


# # -------------------------
# # Runner
# # -------------------------
# async def main():
#     workflow = MainWorkflow()

#     result = await workflow.run(
#         input_msg="Write a article on Finetuning LLM's"
#     )

#     print("\n===== GENERATED ARTICLE =====\n")
#     print(result)


# if __name__ == "__main__":
#     asyncio.run(main())




import asyncio
import os
from dotenv import load_dotenv
from workflows import Workflow, step, Context
from workflows.events import StartEvent, StopEvent
from openai import OpenAI
from individual_functions import Content_grader, Content_writer, Content_changes_proposer, Content_refiner

# -------------------------
# Load environment variables
# -------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
assert OPENAI_API_KEY, "OPENAI_API_KEY not found"

client = OpenAI(api_key=OPENAI_API_KEY)


# -------------------------
# Workflow Definition
# -------------------------
class MainWorkflow(Workflow):

    @step
    async def start(self, ctx: Context, ev: StartEvent) -> StopEvent:
        query = ev.input_msg

        MAX_REFINEMENTS = 3
        THRESHOLD = 9.0

        print(f"\n{'='*80}")
        print(f"STARTING ARTICLE GENERATION WORKFLOW")
        print(f"{'='*80}")
        print(f"Topic: {query}")
        print(f"Threshold: {THRESHOLD}/10")
        print(f"Max Refinements: {MAX_REFINEMENTS}")
        print(f"{'='*80}\n")

        # Step 1: Generate initial article (ONCE, outside loop)
        print(f"[AGENT 1] Generating initial article...")
        article = await Content_writer(query=query)
        print(f"[AGENT 1] ✓ Initial article created ({len(article)} characters)\n")

        best_article = article
        best_score = 0.0
        best_justification = ""
        best_weaknesses = ""

        # Refinement loop - runs from 1 to MAX_REFINEMENTS
        for attempt in range(1, MAX_REFINEMENTS + 1):
            print(f"{'='*80}")
            print(f"ITERATION {attempt}/{MAX_REFINEMENTS}")
            print(f"{'='*80}")
            
            # Step 2: Grade the current article
            print(f"[AGENT 2] Grading article (Attempt {attempt})...")
            score, justification, weaknesses = await Content_grader(
                article_content=article
            )
            print(f"[AGENT 2] Score: {score}/10")
            print(f"[AGENT 2] Justification: {justification[:150]}...")
            
            # Track best version seen so far
            if score > best_score:
                best_score = score
                best_article = article
                best_justification = justification
                best_weaknesses = weaknesses
                print(f"[INFO] ✓ New best score recorded: {best_score}/10")

            # Check if quality threshold is met
            if score >= THRESHOLD:
                print(f"\n{'='*80}")
                print(f"SUCCESS! Article meets quality threshold")
                print(f"{'='*80}")
                print(f"Final Score: {score}/10")
                print(f"Threshold: {THRESHOLD}/10")
                print(f"Total Refinements: {attempt - 1}")
                print(f"{'='*80}\n")
                return StopEvent(result={
                    'article': article,
                    'score': score,
                    'justification': justification,
                    'weaknesses': weaknesses,
                    'attempts': attempt,
                    'refinements': attempt - 1
                })

            # Check if we've reached max attempts
            if attempt >= MAX_REFINEMENTS:
                print(f"\n{'='*80}")
                print(f"MAX REFINEMENTS REACHED")
                print(f"{'='*80}")
                print(f"Returning best version from all attempts")
                print(f"Best Score: {best_score}/10")
                print(f"Total Refinements: {MAX_REFINEMENTS}")
                print(f"{'='*80}\n")
                return StopEvent(result={
                    'article': best_article,
                    'score': best_score,
                    'justification': best_justification,
                    'weaknesses': best_weaknesses,
                    'attempts': MAX_REFINEMENTS,
                    'refinements': MAX_REFINEMENTS
                })

            # Score is below threshold and we have more attempts - refine
            print(f"[INFO] Score {score} < {THRESHOLD}. Refinement needed.")
            print(f"[INFO] Remaining attempts: {MAX_REFINEMENTS - attempt}\n")

            # Step 3: Propose changes
            print(f"[AGENT 3] Analyzing article and proposing improvements...")
            changes = await Content_changes_proposer(
                article_content=article,
                score=score,
                justification=justification,
                weaknesses=weaknesses,
                Threshold=THRESHOLD
            )
            print(f"[AGENT 3] ✓ Changes proposed\n")

            # Step 4: Refine article
            print(f"[AGENT 4] Applying proposed changes to article...")
            article = await Content_refiner(
                changes=changes,
                article_content=article
            )
            print(f"[AGENT 4] ✓ Article refined ({len(article)} characters)")
            print(f"[INFO] Proceeding to next evaluation...\n")

        # This should never be reached due to the return statements above
        # but included as a safety fallback
        return StopEvent(result={
            'article': best_article,
            'score': best_score,
            'justification': best_justification,
            'weaknesses': best_weaknesses,
            'attempts': MAX_REFINEMENTS,
            'refinements': MAX_REFINEMENTS
        })


# -------------------------
# Runner
# -------------------------
async def main():
    print("\n" + "="*80)
    print("ARTICLE GENERATION SYSTEM")
    print("="*80 + "\n")
    
    workflow = MainWorkflow()

    result = await workflow.run(
        input_msg="Write an article on Finetuning LLM's"
    )

    print("\n" + "="*80)
    print("FINAL RESULT")
    print("="*80)
    
    if isinstance(result, dict):
        print(f"\nFinal Score: {result['score']}/10")
        print(f"Total Attempts: {result['attempts']}")
        print(f"Total Refinements: {result['refinements']}")
        print(f"\nJustification:\n{result['justification']}")
        if result.get('weaknesses'):
            print(f"\nWeaknesses:\n{result['weaknesses']}")
        print(f"\n{'='*80}")
        print("ARTICLE CONTENT")
        print(f"{'='*80}\n")
        print(result['article'])
    else:
        # Fallback for simple string result
        print(result)
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(main())