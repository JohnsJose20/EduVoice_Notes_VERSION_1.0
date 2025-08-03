from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from deep_translator import GoogleTranslator
import os
import tempfile
import wave
import io
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
from gtts import gTTS
import base64

app = Flask(__name__)

def generate_structured_notes(text, language="en"):
    """Generate well-formatted study notes with headings and proper punctuation"""
    try:
        # Clean and validate input
        text = ' '.join(text.strip().split())
        if len(text.split()) < 20:  # Require at least 20 words
            if language == 'ml':
                return "📝 കുറിപ്പുകൾ:\n\nനല്ല കുറിപ്പുകൾക്കായി കൂടുതൽ ഉള്ളടക്കം നൽകുക (കുറഞ്ഞത് 4-5 വാക്യങ്ങൾ)."
            elif language == 'hi':
                return "📝 नोट्स:\n\nबेहतर नोट्स के लिए कृपया अधिक सामग्री प्रदान करें (कम से कम 4-5 वाक्य)।"
            elif language == 'kn':
                return "📝 ಟಿಪ್ಪಣಿಗಳು:\n\nಉತ್ತಮ ಟಿಪ್ಪಣಿಗಳಿಗಾಗಿ ದಯವಿಟ್ಟು ಹೆಚ್ಚಿನ ವಿಷಯವನ್ನು ನೀಡಿ (ಕನಿಷ್ಠ 4-5 ವಾಕ್ಯಗಳು)."
            else:
                return "📝 Notes:\n\nPlease provide more content (at least 4-5 sentences) for better notes."
        
        # For non-English languages, we'll use a simpler formatting approach
        if language != 'en':
            return format_non_english_notes(text, language)
        
        # English note generation with sumy
        stemmer = Stemmer('english')
        parser = PlaintextParser.from_string(text, Tokenizer('english'))
        
        if len(text) > 1000:
            summarizer = TextRankSummarizer(stemmer)
            summarizer.stop_words = get_stop_words('english')
            sentence_count = min(8, len(text)//150)
        else:
            summarizer = LsaSummarizer(stemmer)
            summarizer.stop_words = get_stop_words('english')
            sentence_count = min(6, len(text)//100)
        
        summary = summarizer(parser.document, sentence_count)
        points = [str(sentence).capitalize() for sentence in summary]
        
        notes = "📚 Comprehensive Study Notes\n\n"
        notes += "🔍 Core Concepts:\n"
        notes += "\n".join(f"  • {point.rstrip('.')}." for point in points[:3])
        
        if len(points) > 3:
            notes += "\n\n📖 Supporting Details:\n"
            notes += "\n".join(f"  - {point.rstrip('.')}." for point in points[3:-1])
        
        notes += "\n\n💡 Key Takeaways:\n"
        notes += f"  → {points[0].rstrip('.')}.\n"
        if len(points) > 1:
            notes += f"  → {points[-1].rstrip('.')}."
        
        return notes
        
    except Exception as e:
        print(f"Note generation error: {str(e)}")
        return format_fallback_notes(text, language)

def format_non_english_notes(text, language):
    """Format notes for non-English languages without summarization"""
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    if not sentences:
        return format_fallback_notes(text, language)
    
    if language == 'ml':  # Malayalam
        notes = "📚 സമഗ്ര പഠന കുറിപ്പുകൾ\n\n"
        notes += "🔍 പ്രധാന ആശയങ്ങൾ:\n"
        notes += "\n".join(f"  • {s}." for s in sentences[:3])
        
        if len(sentences) > 3:
            notes += "\n\n📖 പിന്തുണയ്ക്കുന്ന വിശദാംശങ്ങൾ:\n"
            notes += "\n".join(f"  - {s}." for s in sentences[3:6])
        
        notes += "\n\n💡 പ്രധാനപ്പെട്ട കാര്യങ്ങൾ:\n"
        notes += f"  → {sentences[0]}.\n"
        if len(sentences) > 1:
            notes += f"  → {sentences[-1]}."
    
    elif language == 'hi':  # Hindi
        notes = "📚 व्यापक अध्ययन नोट्स\n\n"
        notes += "🔍 मुख्य अवधारणाएँ:\n"
        notes += "\n".join(f"  • {s}." for s in sentences[:3])
        
        if len(sentences) > 3:
            notes += "\n\n📖 सहायक विवरण:\n"
            notes += "\n".join(f"  - {s}." for s in sentences[3:6])
        
        notes += "\n\n💡 मुख्य बातें:\n"
        notes += f"  → {sentences[0]}.\n"
        if len(sentences) > 1:
            notes += f"  → {sentences[-1]}."
    
    elif language == 'kn':  # Kannada
        notes = "📚 ಸಮಗ್ರ ಅಧ್ಯಯನ ನೋಟ್ಸ್\n\n"
        notes += "🔍 ಮುಖ್ಯ ಪರಿಕಲ್ಪನೆಗಳು:\n"
        notes += "\n".join(f"  • {s}." for s in sentences[:3])
        
        if len(sentences) > 3:
            notes += "\n\n📖 ಬೆಂಬಲ ವಿವರಗಳು:\n"
            notes += "\n".join(f"  - {s}." for s in sentences[3:6])
        
        notes += "\n\n💡 ಪ್ರಮುಖ ತೆಗೆದುಕೊಳ್ಳುವಿಕೆಗಳು:\n"
        notes += f"  → {sentences[0]}.\n"
        if len(sentences) > 1:
            notes += f"  → {sentences[-1]}."
    
    else:  # Default format for other languages
        notes = "📚 Notes\n\n"
        notes += "🔍 Main Points:\n"
        notes += "\n".join(f"  • {s}." for s in sentences[:3])
        
        if len(sentences) > 3:
            notes += "\n\n📖 Details:\n"
            notes += "\n".join(f"  - {s}." for s in sentences[3:6])
        
        notes += "\n\n💡 Takeaways:\n"
        notes += f"  → {sentences[0]}.\n"
        if len(sentences) > 1:
            notes += f"  → {sentences[-1]}."
    
    return notes

def format_fallback_notes(text, language):
    """Fallback note format when other methods fail"""
    if language == 'ml':
        return "📝 കുറിപ്പുകൾ:\n\n" + text[:1000] + ("[...]" if len(text) > 1000 else "")
    elif language == 'hi':
        return "📝 नोट्स:\n\n" + text[:1000] + ("[...]" if len(text) > 1000 else "")
    elif language == 'kn':
        return "📝 ಟಿಪ್ಪಣಿಗಳು:\n\n" + text[:1000] + ("[...]" if len(text) > 1000 else "")
    else:
        return "📝 Notes:\n\n" + text[:1000] + ("[...]" if len(text) > 1000 else "")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_audio():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file uploaded'}), 400
        
        audio_file = request.files['audio']
        language = request.form.get('language', 'en')
        
        # Validate WAV format
        audio_data = audio_file.read()
        try:
            with io.BytesIO(audio_data) as audio_buffer:
                with wave.open(audio_buffer, 'rb') as wav_file:
                    if wav_file.getnchannels() != 1 or wav_file.getsampwidth() != 2:
                        raise ValueError("Only mono 16-bit WAV files supported")
        except (wave.Error, ValueError):
            return jsonify({'error': 'Invalid WAV format. Use mono 16-bit PCM WAV.'}), 400
        
        # Save temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name
        
        # Speech recognition
        r = sr.Recognizer()
        with sr.AudioFile(tmp_path) as source:
            audio = r.record(source)
            text = r.recognize_google(audio, language=language)
        
        # Translation (skip if already English)
        translation = text
        if language != 'en':
            try:
                translation = GoogleTranslator(source='auto', target='en').translate(text)
            except Exception as e:
                translation = f"{text}\n\n[Translation unavailable: {str(e)}]"
        
        # Generate structured notes in the original language
        short_notes = generate_structured_notes(text, language)
        
        return jsonify({
            'text': text,
            'translation': translation,
            'short_notes': short_notes
        })
        
    except sr.UnknownValueError:
        error_msg = {
            'en': 'Could not understand audio. Speak more clearly.',
            'ml': 'ശബ്ദം മനസ്സിലാക്കാൻ കഴിഞ്ഞില്ല. കൂടുതൽ വ്യക്തമായി സംസാരിക്കുക.',
            'hi': 'ऑडियो समझ नहीं आया। स्पष्ट रूप से बोलें।',
            'kn': 'ಧ್ವನಿಯನ್ನು ಅರ್ಥಮಾಡಿಕೊಳ್ಳಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ಸ್ಪಷ್ಟವಾಗಿ ಮಾತನಾಡಿ.'
        }.get(language, 'Could not understand audio. Speak more clearly.')
        return jsonify({'error': error_msg}), 400
    except sr.RequestError as e:
        return jsonify({'error': f'Speech service error: {str(e)}'}), 503
    except Exception as e:
        return jsonify({'error': f'Processing error: {str(e)}'}), 500
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.route('/generate_speech', methods=['POST'])
def generate_speech():
    try:
        data = request.json
        text = data.get('text', '')
        language = data.get('language', 'en')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Map language codes to gTTS language codes
        lang_map = {
            'ml': 'ml',  # Malayalam
            'hi': 'hi',  # Hindi
            'kn': 'kn',  # Kannada
            'ta': 'ta',  # Tamil
            'te': 'te'   # Telugu
        }
        tts_lang = lang_map.get(language, 'en')
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            tts = gTTS(text=text, lang=tts_lang, slow=False)
            tts.save(tmp.name)
            tmp_path = tmp.name
        
        # Read and encode audio
        with open(tmp_path, 'rb') as f:
            audio_data = f.read()
        
        # Clean up
        os.unlink(tmp_path)
        
        return jsonify({
            'audio': base64.b64encode(audio_data).decode('utf-8'),
            'mimeType': 'audio/mpeg'
        })
        
    except Exception as e:
        return jsonify({'error': f'Speech generation error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)