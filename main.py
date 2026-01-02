import pdfplumber
import pyttsx3

# Step 1: Read PDF
pdf_path = "./pdf_to_speech/sample.pdf"
text = ""

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        extracted_text = page.extract_text()
        if extracted_text:
            text += extracted_text + "\n"

# Step 2: Text to Speech
engine = pyttsx3.init()
engine.save_to_file(text, "output_audio.mp3")
engine.runAndWait()

print("PDF converted to speech successfully!")
