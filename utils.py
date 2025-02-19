import os
from dotenv import load_dotenv
from langdetect import detect, DetectorFactory
from groq import Groq

# Ensure consistent language detection results
DetectorFactory.seed = 0

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize the Groq client
client = Groq(api_key=groq_api_key)

def get_response(question):
    # Detect the language of the question
    lang = detect(question)

    # URLs for reference
    urls = """
    **Relevant Saudi Financial Sources:**
    - [Saudi Exchange](https://www.saudiexchange.sa/wps/portal/saudiexchange?locale=en)
    - [Tadawul Group](https://www.tadawulgroup.sa/wps/portal/tadawulgroup)
    - [Edaa (Securities Depository Center)](https://www.tadawulgroup.sa/wps/portal/tadawulgroup/portfolio/edaa)
    """

    # Set the prompt template with URLs included
    template_en = f"""You are a specialized financial data assistant, designed to provide **accurate**, **precise**, and **up-to-date** information from trusted Saudi sources.

    If the question pertains to topics outside of Saudi financial data, respond with: "I'm trained to provide information exclusively on Saudi financial matters."

    Respond to the following question in a **point-wise format** that highlights key information clearly and succinctly. Avoid lengthy paragraphs. Focus on:
    - **Numerical data**
    - **Market performance**
    - **Trading volume**
    - **Regulatory updates**

    Reference the following sources for your response:
    {urls}

    Start with "Pleased to provide the information you’re looking for!" and provide a confident response.

    Question: {question}

    Answer:
    """

    template_ar = f"""أنت مساعد بيانات مالية متخصص، مصمم لتقديم **معلومات دقيقة**، **حديثة** من **مصادر سعودية موثوقة**.

    إذا كان السؤال يتعلق بمواضيع خارج البيانات المالية السعودية، أجب بعبارة: "أنا مدرب على تقديم المعلومات المتعلقة بالمسائل المالية السعودية فقط."

    أجب على السؤال التالي في **تنسيق نقاط مختصرة** يبرز المعلومات الأساسية بوضوح وباختصار. تجنب الفقرات الطويلة. ركز على:
    - **البيانات الرقمية**
    - **أداء السوق**
    - **حجم التداول**
    - **التحديثات التنظيمية**

    يمكنك الرجوع إلى المصادر التالية:
    {urls}

    ابدأ بعبارة "يسعدني مساعدتك!" وقدم إجابة واثقة.

    السؤال: {question}

    الإجابة:
    """

    # Choose the appropriate prompt template based on language
    prompt_text = template_ar if lang == 'ar' else template_en

    # Groq API call to generate response
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt_text}],
            temperature=1,  
            max_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )

        # Capture streamed response
        response = ""
        for chunk in completion:
            response += chunk.choices[0].delta.content or ""

        # Friendly ending based on language
        response += "\n\nI'm here to help you with any other questions you might have! Feel free to ask. 🌟" if lang != 'ar' else "\n\nيسعدني مساعدتك! 😊"

        return response

    except Exception as e:
        return f"An error occurred: {e}"
