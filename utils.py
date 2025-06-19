
import os
import datetime
from dotenv import load_dotenv
from langdetect import detect, DetectorFactory
from groq import Groq

# Ensure consistent language detection results
DetectorFactory.seed = 0

# Load environment variables
# Hardcoded Groq API Key (⚠️ Use only in development or secured environments)
groq_api_key = "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"


# Initialize the Groq client
client = Groq(api_key=groq_api_key)

def get_response(question):
    # Detect the language of the question
    lang = detect(question)

    # Get today's date dynamically
    current_date = datetime.datetime.now().strftime("%B %d, %Y")  # Example: "February 19, 2025"

    # URLs for reference
    urls = """
    **Relevant Saudi Financial Sources (Updated for 2025):**
    - [Saudi Exchange](https://www.saudiexchange.sa/wps/portal/saudiexchange?locale=en)
    - [Tadawul Group](https://www.tadawulgroup.sa/wps/portal/tadawulgroup)
    - [Edaa (Securities Depository Center)](https://www.tadawulgroup.sa/wps/portal/tadawulgroup/portfolio/edaa)
    """

    # Define common greetings
    greetings_en = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
    greetings_ar = ["مرحبا", "أهلاً", "السلام عليكم", "مساء الخير", "صباح الخير"]

    # Check if the user input is a greeting
    if question.lower() in greetings_en:
        return "Hello! 😊 How can I assist you with Saudi financial data today?"
    elif question.lower() in greetings_ar:
        return "مرحباً! 😊 كيف يمكنني مساعدتك في البيانات المالية السعودية اليوم؟"

    # Set the prompt template with real-time data reference
    template_en = f"""You are a specialized financial data assistant, designed to provide **accurate**, **precise**, and **up-to-date** financial insights from trusted Saudi sources. Your answers should always reflect the latest available market data as of **{current_date}**.

    If the question pertains to topics outside of Saudi financial data, respond with: "I'm trained to provide information exclusively on Saudi financial matters."

    Respond to the following question in a **point-wise format** that highlights key information clearly and succinctly. Avoid lengthy paragraphs. Focus on:
    - **Numerical data**
    - **Market performance**
    - **Trading volume**
    - **Regulatory updates**

    Use the most recent data from the following sources:
    {urls}

    Start with "Pleased to provide the information you’re looking for!" and ensure your response reflects **current market conditions**.

    Question: {question}

    Answer:
    """

    template_ar = f"""أنت مساعد بيانات مالية متخصص، مصمم لتقديم **معلومات دقيقة**، **حديثة** من **مصادر سعودية موثوقة**. يجب أن تعكس إجاباتك أحدث البيانات المالية المتاحة وفقًا للتاريخ **{current_date}**.

    إذا كان السؤال يتعلق بمواضيع خارج البيانات المالية السعودية، أجب بعبارة: "أنا مدرب على تقديم المعلومات المتعلقة بالمسائل المالية السعودية فقط."

    أجب على السؤال التالي في **تنسيق نقاط مختصرة** يبرز المعلومات الأساسية بوضوح وباختصار. تجنب الفقرات الطويلة. ركز على:
    - **البيانات الرقمية**
    - **أداء السوق**
    - **حجم التداول**
    - **التحديثات التنظيمية**

    استخدم أحدث البيانات من المصادر التالية:
    {urls}

    ابدأ بعبارة "يسعدني مساعدتك!" وتأكد من أن إجابتك تعكس **أحدث ظروف السوق**.

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
