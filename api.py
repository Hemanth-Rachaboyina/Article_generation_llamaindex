from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import asyncio
import json
from typing import Optional
import os
from dotenv import load_dotenv
from openai import OpenAI
from individual_functions import Content_grader, Content_writer, Content_changes_proposer, Content_refiner

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
assert OPENAI_API_KEY, "OPENAI_API_KEY not found"

app = FastAPI(title="Article Generator API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ArticleRequest(BaseModel):
    topic: str = Field(..., description="Article topic")
    max_tokens: Optional[int] = Field(1500, description="Maximum tokens for article")
    threshold: Optional[float] = Field(9.0, description="Quality threshold score")
    max_refinements: Optional[int] = Field(3, description="Maximum refinement attempts")

class StatusUpdate(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None

async def generate_article_stream(request: ArticleRequest):
    """Generate article with real-time status updates via Server-Sent Events"""
    
    try:
        # Send initial status
        yield f"data: {json.dumps({'status': 'started', 'message': 'Starting article generation...', 'data': None})}\n\n"
        await asyncio.sleep(0.1)
        
        MAX_REFINEMENTS = request.max_refinements
        THRESHOLD = request.threshold
        query = request.topic
        
        # Step 1: Generate initial article
        yield f"data: {json.dumps({'status': 'writing', 'message': 'Agent 1: Writing initial article...', 'data': {'attempt': 0}})}\n\n"
        await asyncio.sleep(0.1)
        
        article = await Content_writer(query=query)
        
        yield f"data: {json.dumps({'status': 'written', 'message': 'Agent 1: Initial article completed!', 'data': {'article_length': len(article), 'attempt': 0}})}\n\n"
        await asyncio.sleep(0.1)
        
        best_article = article
        best_score = 0.0
        best_justification = ""
        best_weaknesses = ""
        
        # Refinement loop - will run MAX_REFINEMENTS times or until threshold is met
        for attempt in range(1, MAX_REFINEMENTS + 1):
            # Grade the current article
            yield f"data: {json.dumps({'status': 'grading', 'message': f'Agent 2: Grading article (Attempt {attempt}/{MAX_REFINEMENTS})...', 'data': {'attempt': attempt}})}\n\n"
            await asyncio.sleep(0.1)
            
            score, justification, weaknesses = await Content_grader(
                article_content=article
            )
            
            yield f"data: {json.dumps({'status': 'graded', 'message': f'Agent 2: Score is {score}/10', 'data': {'score': score, 'attempt': attempt, 'threshold': THRESHOLD}})}\n\n"
            await asyncio.sleep(0.1)
            
            # Track best version seen so far
            if score > best_score:
                best_score = score
                best_article = article
                best_justification = justification
                best_weaknesses = weaknesses
                yield f"data: {json.dumps({'status': 'info', 'message': f'✓ New best score: {best_score}/10', 'data': {'best_score': best_score}})}\n\n"
                await asyncio.sleep(0.1)
            
            # Check if quality threshold is met
            if score >= THRESHOLD:
                yield f"data: {json.dumps({'status': 'success', 'message': f'🎉 Article meets quality threshold! ({score} >= {THRESHOLD})', 'data': {'score': score, 'threshold': THRESHOLD}})}\n\n"
                await asyncio.sleep(0.1)
                
                yield f"data: {json.dumps({'status': 'completed', 'message': f'Final article ready with score {score}/10', 'data': {'final_score': score, 'article': article, 'justification': justification, 'weaknesses': weaknesses, 'attempts': attempt, 'total_refinements': attempt - 1}})}\n\n"
                return
            
            # If we've reached max refinements, return best version
            if attempt >= MAX_REFINEMENTS:
                yield f"data: {json.dumps({'status': 'max_reached', 'message': f'⚠️ Max refinements ({MAX_REFINEMENTS}) reached. Returning best version.', 'data': {'best_score': best_score}})}\n\n"
                await asyncio.sleep(0.1)
                
                yield f"data: {json.dumps({'status': 'completed', 'message': f'Final article (best of {MAX_REFINEMENTS} attempts) with score {best_score}/10', 'data': {'final_score': best_score, 'article': best_article, 'justification': best_justification, 'weaknesses': best_weaknesses, 'attempts': MAX_REFINEMENTS, 'total_refinements': MAX_REFINEMENTS}})}\n\n"
                return
            
            # Score is below threshold and we have more attempts - refine the article
            yield f"data: {json.dumps({'status': 'below_threshold', 'message': f'Score {score} < {THRESHOLD}. Initiating refinement {attempt}/{MAX_REFINEMENTS}...', 'data': {'score': score, 'threshold': THRESHOLD}})}\n\n"
            await asyncio.sleep(0.1)
            
            # Agent 3: Propose changes
            yield f"data: {json.dumps({'status': 'proposing', 'message': f'Agent 3: Analyzing and proposing improvements...', 'data': {'attempt': attempt}})}\n\n"
            await asyncio.sleep(0.1)
            
            changes = await Content_changes_proposer(
                article_content=article,
                score=score,
                justification=justification,
                weaknesses=weaknesses,
                Threshold=THRESHOLD
            )
            
            yield f"data: {json.dumps({'status': 'proposed', 'message': f'Agent 3: Changes proposed successfully', 'data': {'attempt': attempt}})}\n\n"
            await asyncio.sleep(0.1)
            
            # Agent 4: Refine the article
            yield f"data: {json.dumps({'status': 'refining', 'message': f'Agent 4: Refining article (Refinement {attempt}/{MAX_REFINEMENTS})...', 'data': {'attempt': attempt}})}\n\n"
            await asyncio.sleep(0.1)
            
            article = await Content_refiner(
                changes=changes,
                article_content=article
            )
            
            yield f"data: {json.dumps({'status': 'refined', 'message': f'Agent 4: Refinement {attempt} complete. Re-evaluating...', 'data': {'attempt': attempt}})}\n\n"
            await asyncio.sleep(0.1)
            
            # Loop will continue to grade the refined article in the next iteration
        
        # This should never be reached due to the return statements above
        # but included for safety
        yield f"data: {json.dumps({'status': 'completed', 'message': f'Article generation complete', 'data': {'final_score': best_score, 'article': best_article, 'justification': best_justification, 'weaknesses': best_weaknesses, 'attempts': MAX_REFINEMENTS, 'total_refinements': MAX_REFINEMENTS}})}\n\n"
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        yield f"data: {json.dumps({'status': 'error', 'message': f'Error: {str(e)}', 'data': {'error_details': error_details}})}\n\n"

@app.post("/api/generate-article")
async def generate_article(request: ArticleRequest):
    """Stream article generation with real-time updates"""
    return StreamingResponse(
        generate_article_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable proxy buffering
        }
    )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Article Generator API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)