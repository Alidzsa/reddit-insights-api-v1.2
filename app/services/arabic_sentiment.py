import re

class ArabicSentiment:
    """
    Lightweight rule-based sentiment analysis for Arabic/Darija.
    In a full production environment, this would be replaced by a 
    HuggingFace model (e.g., CAMeL-BERT).
    """
    def __init__(self):
        # Advanced positive/negative lexicon for Arabic/Darija/Algerian
        self.positive_words = {
            "جميل", "رائع", "ممتاز", "مليح", "هايل", "فور", "باهي", 
            "شكرا", "مبروك", "ناجح", "قوي", "مفيد", "جيد", "تحيا",
            "الله يحفظك", "يعطيك الصحة", "مشاء الله", "تبارك الله",
            "بزاف مليح", "منيح", "لاباس", "غابة", "توب", "top", "nice",
            "صاحيت", "يعطيك العافية", "زين", "غالي", "كبير"
        }
        self.negative_words = {
            "سيء", "رديء", "خايب", "ماشي مليح", "ضعيف", "مشكل", 
            "صعب", "فاشل", "ممل", "حزين", "خسارة", "زفت", "حقرة",
            "كرهت", "عييت", "تبا", "خسيس", "مكاش منها", "ماكان والو",
            "رخيص", "حرام", "عيب", "صغير", "ناقص", "غلط", "كذب",
            "نكره", "دزي معاهم", "بهدلة", "حاشاك", "قبيح"
        }
        self.intensifiers = {"بزاف", "قاع", "بزاف بزاف", "جدا", "كلش"}
        self.negations = {"مش", "ماشي", "ماكانش", "لا", "ما"}

    def analyze(self, text: str) -> float:
        """
        Calculates sentiment with basic negation and intensification logic.
        """
        if not text:
            return 0.0
            
        words = re.findall(r'\w+', text.lower())
        score = 0
        negate = False
        
        for i, word in enumerate(words):
            # Check negation
            if word in self.negations:
                negate = True
                continue
            
            # Check sentiment
            current_val = 0
            if word in self.positive_words:
                current_val = 1
            elif word in self.negative_words:
                current_val = -1
            
            if current_val != 0:
                # Apply negation
                if negate:
                    current_val *= -1
                    negate = False
                
                # Apply intensification
                if i > 0 and words[i-1] in self.intensifiers:
                    current_val *= 1.5
                
                score += current_val
        
        # Normalize score
        if not words:
            return 0.0
        return max(-1.0, min(1.0, score / (len(words) / 5 + 1)))

arabic_sentiment = ArabicSentiment()
