from langchain_groq import ChatGroq
from langchain_community.chat_models import ChatOpenAI
from dotenv import load_dotenv
import os
import random
import faiss
from sentence_transformers import SentenceTransformer
import json

load_dotenv()

FAISS_INDEX_FILE = "faiss_quotes_index.bin"
QUOTES_FILE = "quotes.json"

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
dimension = embedding_model.get_sentence_embedding_dimension()

if os.path.exists(FAISS_INDEX_FILE) and os.path.exists(QUOTES_FILE):
    faiss_index = faiss.read_index(FAISS_INDEX_FILE)    
    with open(QUOTES_FILE, "r") as f:
        stored_quotes = json.load(f)
else:
    faiss_index = faiss.IndexFlatL2(dimension)
    stored_quotes = []

def save_state():
    """Persist FAISS index and quotes to disk."""
    faiss.write_index(faiss_index, FAISS_INDEX_FILE)
    with open(QUOTES_FILE, "w") as f:
        json.dump(stored_quotes, f)


def is_quote_unique(quote, threshold=0.9):
    """Check if a quote is unique using FAISS."""
    if len(stored_quotes) == 0:
        return True  # No quotes stored yet
    embedding = embedding_model.encode([quote])
    distances, _ = faiss_index.search(embedding, 1)
    return distances[0][0] > (1 - threshold)  # Lower distance indicates higher similarity

def add_quote_to_memory(quote):
    """Add a quote to FAISS and the stored quotes list."""
    embedding = embedding_model.encode([quote])
    faiss_index.add(embedding)
    stored_quotes.append(quote)
    save_state()

def GetPhilosopher():
    names = [
        "Socrates", "Plato", "Aristotle", "Confucius", "Laozi", "Zeno of Citium", 
        "Augustine of Hippo", "Boethius", "Avicenna (Ibn Sina)", "Thomas Aquinas", 
        "René Descartes", "John Locke", "David Hume", "Immanuel Kant", 
        "Friedrich Nietzsche", "Karl Marx", "Søren Kierkegaard", "Jean-Paul Sartre", 
        "Simone de Beauvoir", "Ludwig Wittgenstein", "Michel Foucault", 
        "Jacques Derrida", "Hannah Arendt", "Martin Heidegger", "Baruch Spinoza", 
        "Gottfried Wilhelm Leibniz", "Arthur Schopenhauer", "John Stuart Mill", 
        "Georg Wilhelm Friedrich Hegel", "Bertrand Russell"
    ]
    return random.choice(names)

# def quote_generator(philosopher):
#     llm = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY"))
#     prompt = f"""Generate a LIST of 20 quotes by {philosopher} that is inspiring and thought-provoking. Make it so the quote is engaging and can be understood by a wide audience. The quote should be short and impactful.
#                 ONLY GIVE ME THE QUOTE AND NOTHING ELSE"""
#     response = llm.invoke(prompt).content
#     llm2 = ChatOpenAI(model="gpt-4o-mini", temperature=0.6, api_key=os.getenv("OPENAI_API_KEY"))
#     prompt2 = f"""From this list: {response}, choose one quote. ONLY GIVE ME THE QUOTE"""
#     response2 = llm2.invoke(prompt2).content
#     return response2

def quote_generator(philosopher):
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""Generate a LIST of 20 quotes by {philosopher} that is inspiring and thought-provoking. 
                Make it so the quote is engaging and can be understood by a wide audience. 
                The quote should be short and impactful.
                ONLY GIVE ME THE QUOTES AND NOTHING ELSE."""
    response = llm.invoke(prompt).content

    tried_quotes = ""
    llm2 = ChatOpenAI(model="gpt-4o-mini", temperature=0.6, api_key=os.getenv("OPENAI_API_KEY"))
    prompt2 = f"""From this list: {response}, choose one quote or think of another one. ONLY GIVE ME THE QUOTE."""
    
    while True:
        response2 = llm2.invoke(prompt2).content.strip()
        
        # Check if the quote is unique
        if is_quote_unique(response2):
            add_quote_to_memory(response2)
            return response2
        else:
            tried_quotes += response2 + ", "
            prompt2 = f"""From this list: {response}, choose one quote or think of another one. ONLY GIVE ME THE QUOTE. 
            There are some of the quotes that you tried but were already used: {tried_quotes}"""


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
        "pokimane", "snoop-dogg", "stephen-hawking", "taylor-swift",
        "warren-buffett", "will-smith"
    ]
    return random.choice(voices)

def make_caption(topic, description):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""Generate a caption for a post about {topic} and his quote "{description}.
    The caption should be engaging and informative explaining the quote. Make it short, impactful, engaging, and simple to understand.
    It should also have some relevant hashtags. Here are some you can use: #motivation #quotes #positivequotes #selfimprovement #mindset #growthmindset #discipline #proveyourself #inspirationalquotes #inspiration. ONLY GIVE ME THE CAPTION"""
    response = llm.invoke(prompt).content
    return f"{description} - {topic}. \n\n {response} \n\n Remember to like and follow for more!"

def play_situation_maker(quote):
    llm = ChatOpenAI(model="gpt-4o", temperature=0.6, api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""
    You are a creative writer tasked with coming up with humorous, short scenarios. Each scenario should:
    Feature two characters (e.g., a teacher and Me, a boss and Me, Bro and Me) in a brief dialogue.
    Begin with the authority figure asking a serious or straightforward question or making a statement (e.g., “Why are you always late?”).
    Have the Protagonist (Me) respond with the quote: "{quote}".
    Then End with the phrase: "The state I left the <CHARACTER NUM 1> in:" ONLY FILLING IN THE BLANK WITH THE CHARACTER'S NAME (e.g., "The state I left the teacher in:") and nothing else
    Make the situation engaging and relatable to a wide audience and be something which the quote helps to solve.
    ONLY RETURN THE SITUATION, DO NOT EXPLAIN OR ADD ANYTHING ELSE
    MAKE THE SITUATION SOMETHING THAT CAN BE SOLVED WITH THE QUOTE, RELATABLE, AND REALISTIC,
    JUST GIVE ME ONE SCENARIO
    """
    # llm2 = ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))
    # prompt = f"""Take a look at this output from the prompt: "You are a creative writer tasked with coming up with humorous, short scenarios. Each scenario should:
    # Feature two characters (e.g., a teacher and Me, a boss and Me, Bro and Me) in a brief dialogue.
    # Begin with the authority figure asking a serious or straightforward question or making a statement (e.g., “Why are you always late?”).
    # Have the Protagonist (Me) respond with the quote: "{quote}".
    # Then End with the phrase: "The state I left the <CHARACTER NUM 1> in:" ONLY FILLING IN THE BLANK WITH THE CHARACTER'S NAME (e.g., "The state I left the teacher in:") and nothing else
    # Make the situation engaging and relatable to a wide audience and be something which the quote helps to solve.
    # ONLY RETURN THE SITUATION, DO NOT EXPLAIN OR ADD ANYTHING ELSE
    # MAKE THE SITUATION SOMETHING THAT CAN BE SOLVED WITH THE QUOTE AND IS RELATABLE,
    # JUST GIVE ME ONE SCENARIO"
    # {llm.invoke(prompt).content}
    
    # if it is good then return it, otherwise return a new one"""
    
    response = llm.invoke(prompt).content.replace("*","")
    return response

def situation_maker(quote):
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""Fill in the blank: "<BLANK1> when he is <BLANK2> and I hit him with "{quote}""
    \n
    BLANK1 is a person (e.g., Bro, My Teacher, My Boss, etc.)
    BLANK2 is a feeling (e.g., angry, tired, etc.)
    The situation should be engaging and relatable to a wide audience and be something which the quote helps to solve.
    ONLY RETURN THE FILLED IN SENTENCE, DO NOT EXPLAIN OR ADD ANYTHING ELSE"""
    response = llm.invoke(prompt).content
    # response = "Me when bro hits me with " + quote
    return response
    
if __name__ == "__main__":
    topic = "Cathedrals of the Deep Sea"
    voice = determine_voice()
    final_description = refine_description(topic, voice)
    print(f"Topic: {topic}\nVoice: {voice} \n Description: {final_description}")
