from enum import Enum
from typing import List
from pydantic import BaseModel
import asyncio
from pydantic import BaseModel, Field
from workflows import Context, Workflow, step
from workflows.events import Event, StartEvent, StopEvent
from openai import OpenAI
import os
from dotenv import load_dotenv
from prompts import Article_Generator_Prompt, Article_scorer_Prompt , Article_changes_proposer_prompt, Refined_Article_Prompt,model
import uuid
# from llama_index.core.llms import ChatMessage
# from llama_index.core.memory import ChatMemoryBuffer
# from llama_index.core.llms import ChatMessage, MessageRole
from memory_management import  read_memory , to_openai_messages , append_qa


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class Agent1(BaseModel):
    output : str

class Agent2(BaseModel):
    score : int
    justification : str
    weakness : str
class Agent3(BaseModel):
    output : str




# tone, word_count, should be added for more flexibility
async def Content_writer(query:str):
    """
    function for article content generation
    """
    print("Entered Content Generator Function")
    print("Writing the Article .......")
    completion = client.chat.completions.parse(
            model="gpt-4o",
            messages=[
                # *to_openai_messages(read_memory()),
                {"role": "system", "content": Article_Generator_Prompt},
                {"role": "user", "content": query},
            ],
            response_format=Agent1,
        )

    answer = completion.choices[0].message.parsed.output

    print("Hurray!!!!! , Completed Writing the Article ")

    print("Sitback and relax while we generate outstanding article for you ......................")

    return answer


async def Content_grader(article_content:str):
    """
    function for scoring article content.
    """
    print("Entered Content Grader Function")
    print("Grading the Article ......")
    completion = client.chat.completions.parse(
            model=model,
            messages=[
                # *to_openai_messages(read_memory()),
                {"role": "system", "content": Article_scorer_Prompt},
                {"role": "user", "content": article_content},
            ],
            response_format=Agent2,
        )

    answer = completion.choices[0].message.parsed


    print(f"completed grading , score is {answer.score} ")


    return answer.score , answer.justification , answer.weakness





async def Content_changes_proposer(article_content:str , score :int , justification: str , weaknesses : str , Threshold:int):
    """
    function for scoring article content.
    """
    print(f"Oh......! , it seems to be article acheived a score less than {Threshold} , No worries , getting that fixed ")
    print("Proposing Changes .........")
    
    completion = client.chat.completions.parse(
            model=model,
            messages=[
                # *to_openai_messages(read_memory()),
                {"role": "system", "content": Article_changes_proposer_prompt},
                {"role": "user", "content": article_content + f"Score : {score}" + "Justifications : " + justification + "weaknesses:" + weaknesses},
            ],
            response_format=Agent3,
        )

    answer = completion.choices[0].message.parsed.output


    print("Wow! , Amazing Changes are proposed, Amazing Article is on your way")

    return answer





async def Content_refiner(article_content:str ,changes:str):
    """
    function for scoring article content.
    """
    print("Refining the Article in Best possible way ......")
    print("Almost Done !")
    
    completion = client.chat.completions.parse(
            model="gpt-4.1",
            messages=[
                # *to_openai_messages(read_memory()),
                {"role": "system", "content": Refined_Article_Prompt},
                {"role": "user", "content": article_content + "changes_proposed :" + changes},
            ],
            response_format=Agent1,
        )

    answer = completion.choices[0].message.parsed.output


    print("Completed ! , Re-evaluating the Article......")

    return answer





