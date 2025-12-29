"""
Test script to verify the refinement loop works correctly
Run this to test the workflow without the API
"""
import asyncio
import os
from dotenv import load_dotenv
from individual_functions import Content_grader, Content_writer, Content_changes_proposer, Content_refiner

load_dotenv()

async def test_workflow():
    query = "Write an article on Finetuning LLM's"
    MAX_REFINEMENTS = 3
    THRESHOLD = 9.0
    
    print("="*80)
    print("ARTICLE GENERATION WORKFLOW TEST")
    print("="*80)
    print(f"Topic: {query}")
    print(f"Threshold: {THRESHOLD}/10")
    print(f"Max Refinements: {MAX_REFINEMENTS}")
    print("="*80)
    
    # Step 1: Initial article generation
    print("\n[AGENT 1] Writing initial article...")
    article = await Content_writer(query=query)
    print(f"[AGENT 1] ✓ Article written ({len(article)} characters)")
    
    best_article = article
    best_score = 0.0
    best_justification = ""
    best_weaknesses = ""
    
    # Refinement loop
    for attempt in range(1, MAX_REFINEMENTS + 1):
        print(f"\n{'='*80}")
        print(f"REFINEMENT CYCLE {attempt}/{MAX_REFINEMENTS}")
        print(f"{'='*80}")
        
        # Grade the article
        print(f"[AGENT 2] Grading article (Attempt {attempt})...")
        score, justification, weaknesses = await Content_grader(article_content=article)
        print(f"[AGENT 2] Score: {score}/10")
        print(f"[AGENT 2] Justification: {justification[:100]}...")
        
        # Track best version
        if score > best_score:
            best_score = score
            best_article = article
            best_justification = justification
            best_weaknesses = weaknesses
            print(f"[INFO] ✓ New best score: {best_score}/10")
        
        # Check if threshold is met
        if score >= THRESHOLD:
            print(f"\n[SUCCESS] 🎉 Article meets threshold! ({score} >= {THRESHOLD})")
            print(f"[RESULT] Final article ready after {attempt} attempt(s)")
            print(f"[RESULT] Total refinements: {attempt - 1}")
            print(f"[RESULT] Final score: {score}/10")
            break
        
        # Check if max refinements reached
        if attempt >= MAX_REFINEMENTS:
            print(f"\n[WARNING] ⚠️ Max refinements ({MAX_REFINEMENTS}) reached")
            print(f"[RESULT] Returning best version: {best_score}/10")
            print(f"[RESULT] Total refinements: {MAX_REFINEMENTS}")
            break
        
        # Need to refine
        print(f"\n[INFO] Score {score} < {THRESHOLD}. Refinement needed...")
        
        # Agent 3: Propose changes
        print(f"[AGENT 3] Analyzing article and proposing changes...")
        changes = await Content_changes_proposer(
            article_content=article,
            score=score,
            justification=justification,
            weaknesses=weaknesses,
            Threshold=THRESHOLD
        )
        print(f"[AGENT 3] ✓ Changes proposed ({len(changes)} characters)")
        
        # Agent 4: Refine article
        print(f"[AGENT 4] Refining article with proposed changes...")
        article = await Content_refiner(
            changes=changes,
            article_content=article
        )
        print(f"[AGENT 4] ✓ Article refined ({len(article)} characters)")
        print(f"[INFO] Proceeding to next evaluation cycle...")
    
    print("\n" + "="*80)
    print("WORKFLOW COMPLETE")
    print("="*80)
    print(f"Best Score Achieved: {best_score}/10")
    print(f"Article Length: {len(best_article)} characters")
    print(f"Word Count: {len(best_article.split())} words")
    print("="*80)
    
    return best_article, best_score, best_justification

if __name__ == "__main__":
    print("\nStarting workflow test...\n")
    result = asyncio.run(test_workflow())
    print("\n✅ Test completed successfully!")