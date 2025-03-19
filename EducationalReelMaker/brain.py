from langchain_groq import ChatGroq
from langchain_community.chat_models import ChatOpenAI
from dotenv import load_dotenv
import os
import random
import faiss
from sentence_transformers import SentenceTransformer
import json
import numpy as np

load_dotenv()

FAISS_INDEX_FILE = "faiss_index.bin"
TOPICS_FILE = "topics.json"

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
dimension = embedding_model.get_sentence_embedding_dimension()

predefined_topics = [
    "The science behind why cats purr.",
    "The evolution of dance moves from the 1920s to today.",
    "The phenomenon of bioluminescent waves in ocean water.",
    "The history and significance of the 'Psychedelic Art Movement' in the 1960s.",
    "The science behind why leaves change color in the fall.",
    "The science behind how hummingbirds hover in mid-air.",
    "The history of the 'Mona Lisa' and its mysterious smile.",
    "The influence of the color blue in ancient Egyptian art and culture.",
    "The science behind the 'Tetris Effect' and how gaming can influence perception and memory.",
    "The impact of the 'Brown Marmorated Stink Bug' on agriculture and its unexpected origins.",
    "The history of the 'Dopamine Detox' trend and its psychological implications.",
    "The science behind how bubble tea is made and why tapioca pearls are chewy.",
    "The science of bioluminescent organisms and how they create their glow.",
    "The science behind the phenomenon of 'phantom vibrations' when your phone buzzes but it hasn’t.",
    "The history of the color blue in art and its significance throughout different cultures.",
    "The evolution of the electric guitar in rock music.",
    "The history of the 'Dunning-Kruger Effect' and its impact on decision-making.",
    "The history of the 'Dancing Plague' of 1518 in Strasbourg.",
]

if os.path.exists(FAISS_INDEX_FILE) and os.path.exists(TOPICS_FILE):
    # Load FAISS index
    faiss_index = faiss.read_index(FAISS_INDEX_FILE)

    # Load topics
    with open(TOPICS_FILE, "r") as f:
        topic_memory = json.load(f)
else:
    # Create a new FAISS index
    faiss_index = faiss.IndexFlatL2(dimension)

    # Add predefined topics to memory
    topic_memory = []
    for topic in predefined_topics:
        embedding = embedding_model.encode([topic])
        faiss_index.add(embedding)
        topic_memory.append(topic)

    # Save initialized data
    faiss.write_index(faiss_index, FAISS_INDEX_FILE)
    with open(TOPICS_FILE, "w") as f:
        json.dump(topic_memory, f)

# Functions to manage memory
def add_to_memory(topic):
    """Add a topic to FAISS and save to disk."""
    embedding = embedding_model.encode([topic])
    faiss_index.add(embedding)
    topic_memory.append(topic)
    # Persist data
    faiss.write_index(faiss_index, FAISS_INDEX_FILE)
    with open(TOPICS_FILE, "w") as f:
        json.dump(topic_memory, f)

def is_similar_to_memory(topic, threshold=0.8):
    """Check if a topic is similar to stored topics."""
    if len(topic_memory) == 0:
        return False
    embedding = embedding_model.encode([topic])
    distances, _ = faiss_index.search(embedding, 1)
    return distances[0][0] < (1 - threshold)  # Adjust threshold as needed

def topic_identifier():
    llm = ChatGroq(model="llama3-8b-8192", temperature=1, api_key=os.getenv("GROQ_API_KEY"))
    prompt = """
    Pick a random topic and write about it in an engaging way. Give me just the topic no other words, and I'll take care of the rest
    The topic can be in the fields of: science, history, technology, art, music, philosophy, nature, sports, or pop culture.
    Make the topic as specific as possible, and avoid general topics like "the universe" or "the internet".
    Give me a list of topics that will do well as instagram reels.
    Make it so the topics are those that would be interesting to those on instragram reels and can be explained in a short video.
    Choose Simple Topics that can be explained in 10-20 seconds.
    """
    response = llm.invoke(prompt).content
    previous_tries = ""
    
    prompt_2 = f"""
        Take a look at this list for inspiration {response} and pick a topic that you think will do well as an instagram reel.
        Take a look at the ideas, and think of some yourself.
        Only return 1 topic.
        Make the topic as specific as possible, and avoid general topics like "the universe" or "the internet".
        The topic can be in the fields of: science, history, technology, art, music, philosophy, nature, sports, or pop culture.
        Make it so the topic is interesting to those on instragram reels and can be explained in a short video.
        Choose a topic that can be explained in 10-20 seconds.
        RETURN JUST THE TOPIC AND NOTHING ELSE.
    """
    
    while True:
        llm2 = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY"))
        
        response_2 = llm2.invoke(prompt_2).content.strip()

        if not is_similar_to_memory(response_2):
            add_to_memory(response_2)
            break
        else:
            previous_tries += f"{response_2}\n"
            prompt_2 = f"""
            Take a look at this list for inspiration {response} and pick a topic that you think will do well as an instagram reel.
            Take a look at the ideas, and think of some yourself.
            Only return 1 topic.
            Make the topic as specific as possible, and avoid general topics like "the universe" or "the internet".
            The topic can be in the fields of: science, history, technology, art, music, philosophy, nature, sports, or pop culture.
            Make it so the topic is interesting to those on instragram reels and can be explained in a short video.
            Choose a topic that can be explained in 10-20 seconds.
            RETURN JUST THE TOPIC AND NOTHING ELSE.
            HERE ARE SOME PREVIOUS TRIES: {previous_tries}. DO NOT USE THESE IDEAS AGAIN.
            """
    return response_2

# def topic_identifier():
#     llm = ChatGroq(model="llama3-8b-8192", temperature=1, api_key=os.getenv("GROQ_API_KEY"))
#     prompt = """
#     Pick a random topic and write about it in an engaging way. Give me just the topic no other words, and I'll take care of the rest
#     The topic can be in the fields of: science, history, technology, art, music, philosophy, nature, sports, or pop culture.
#     Make the topic as specific as possible, and avoid general topics like "the universe" or "the internet".
#     Give me a list of topics that will do well as instragram reels.
#     Make it so the topics are those that would be interesting to those on instragram reels and can be explained in a short video.
#     Choose Simple Topics that can be explained in 10-20 seconds.
#     """
#     response = llm.invoke(prompt).content
    
#     llm2 = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY"))
#     prompt_2 = """
#     Take a look at this list for inspiration and pick a topic that you think will do well as an instagram reel.
#     Take a look at the ideas, and think of some yourself.
#     Only return 1 topic.
#     Make the topic as specific as possible, and avoid general topics like "the universe" or "the internet".
#     The topic can be in the fields of: science, history, technology, art, music, philosophy, nature, sports, or pop culture.
#     Make it so the topic is interesting to those on instragram reels and can be explained in a short video.
#     Choose a topic that can be explained in 10-20 seconds.
#     RETURN JUST THE TOPIC AND NOTHING ELSE.
#     """
#     response_2 = llm2.invoke(prompt_2).content
#     return response_2

def refine_description(topic, speaker, max_iterations=3):
    """
    Generates a pithy description of the given topic using an iterative refinement process.

    Args:
        topic (str): The topic to describe.
        max_iterations (int): Maximum number of refinement iterations.

    Returns:
        str: Final pithy description of the topic.
    """
    generator_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.4, api_key=os.getenv("OPENAI_API_KEY"))
    # ChatGroq(model="llama3-8b-8192", temperature=0.3, api_key=os.getenv("GROQ_API_KEY"))
    evaluator_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

    # ChatGroq(model="llama3-8b-8192", temperature=0, api_key=os.getenv("GROQ_API_KEY"))

    # Step 1: Generate initial description
    generator_prompt = f"Write a very pithy description using simple words about the topic as if {speaker} was an expert and was explaining it to me a beginner with no knowledge in '{topic}'. Explain it in a easy to understand and that appeals to those at a 6th grade reading level. Make it so the decription can be said in 10-20 seconds. Start with 'Lets talk about' and then the topic. AFTER THAT, TALK ABOUT THE TOPIC AND NOT WHAT YOU ARE GOING TO TELL ME"
    current_description = generator_llm.invoke(generator_prompt).content
    
    for iteration in range(max_iterations):
        # Step 2: Evaluate the description
        evaluator_prompt = (
            f"Evaluate the following description of the topic '{topic}' and NOT THE TITLE OF THE TOPIC ITSELF:\n\n"
            f"\"{current_description}\"\n\n"
            "Provide feedback and, if necessary, rewrite it to make it more pithy, accurate, and engaging"
        )
        updated_description = evaluator_llm.invoke(evaluator_prompt).content
        
        # Step 3: Check if the evaluator suggests any changes
        if updated_description.strip() == current_description.strip():
            # print(f"Accepted after {iteration + 1} iteration(s).")
            return current_description.strip()
        
        # Step 4: Update the current description for the next iteration
        current_description = updated_description
    
    # print(f"Final description after {max_iterations} iterations:")
    final_prompt = (
        f"Here is the topic: '{topic}' and the refined description: '{current_description}'.\n"
        "Please JUST give me the final rewritten description. Thank you!"
        "Do not start with Here is the topic: or anything else, just the description."
    )
    final_description = evaluator_llm.invoke(final_prompt).content.strip()
    return final_description

def determine_voice():
    voices = [
        "alex-jones", "andrew-tate",
        "ariana-grande", "arnold-schwarzenegger",
        "ben-shapiro", "bernie-sanders", "beyonce", "bill-clinton", "bill-gates", 
        "conor-mcgregor", "dj-khaled", "donald-trump",
        "dr-phil", "drake", "dwayne-johnson", "ellen-degeneres",
        "elon-musk", "emma-watson", "greta-thunberg",
        "hillary-clinton", "jeff-bezos", "jerry-seinfeld",
        "jim-cramer", "joe-biden", "joe-rogan", "john-cena", "jordan-peterson",
        "justin-bieber", "kamala-harris", "kanye-west", "kevin-hart",
        "lex-fridman", "lil-wayne", "mark-zuckerberg",
        "mike-tyson", "morgan-freeman",
        "pokimane", "snoop-dogg", "taylor-swift",
        "warren-buffett", "will-smith"
    ]
    return random.choice(voices)

def make_caption(topic, description):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""Generate a caption for a post about {topic} and description "{description}.
    It should also have some relevant hashtags about things like learning and the topic at hand. ONLY GIVE ME THE CAPTION"""
    response = llm.invoke(prompt).content
    return f"{response} \n\n Remember to like and follow for more!"
    # return f"Let's talk about {topic}! {description} Remember to like and follow for more!"
    
if __name__ == "__main__":
    print(is_similar_to_memory("The Science Behind Color-Changing Chameleons"))
    #    topic = "Cathedrals of the Deep Sea"
#    voice = determine_voice()
#    final_description = refine_description(topic, voice)
#    print(f"Topic: {topic}\nVoice: {voice} \n Description: {final_description}")
