from llama_index.core.llms import ChatMessage
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole


from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage, MessageRole





# memory = ChatMemoryBuffer.from_defaults(token_limit=40000)



def to_openai_messages(messages):
    return [
        {
            "role": msg.role.value,
            "content": msg.content
        }
        for msg in messages
    ]

# memory/memory_management.py


# Singleton memory instance (per process / per session)
_memory = None


def init_memory(token_limit: int = 40000):
    global _memory
    if _memory is None:
        _memory = ChatMemoryBuffer.from_defaults(
            token_limit=token_limit
        )
    return _memory


def get_memory():
    if _memory is None:
        raise RuntimeError("Memory not initialized. Call init_memory() first.")
    return _memory


def read_memory():
    """Read-only access for agents."""
    return get_memory().get()


def append_qa(question: str, answer: str):
    """Explicit write — used ONLY by final agent."""
    mem = get_memory()
    mem.put(ChatMessage(
        role=MessageRole.USER,
        content=question
    ))
    mem.put(ChatMessage(
        role=MessageRole.ASSISTANT,
        content=answer
    ))

