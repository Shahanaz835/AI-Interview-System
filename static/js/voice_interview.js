/**
 * AI Interviewer - Real-Time Voice Interaction Engine
 * Powered by Web Speech API (SpeechRecognition STT & SpeechSynthesis TTS)
 */

class VoiceInterviewer {
    constructor(config) {
        this.sessionId = config.sessionId;
        this.currentQuestionId = config.questionId;
        this.currentQuestionNumber = config.questionNumber;
        this.totalQuestions = config.totalQuestions;
        this.csrfToken = config.csrfToken;
        
        // DOM Elements
        this.micBtn = document.getElementById('micToggleBtn');
        this.micStatus = document.getElementById('micStatusText');
        this.transcriptInput = document.getElementById('answerTranscript');
        this.submitBtn = document.getElementById('submitAnswerBtn');
        this.aiSpeakingIndicator = document.getElementById('aiSpeakingIndicator');
        this.replayQuestionBtn = document.getElementById('replayQuestionBtn');
        this.questionTextElem = document.getElementById('currentQuestionText');
        this.questionNumberElem = document.getElementById('questionBadgeNumber');
        this.evaluationModal = new bootstrap.Modal(document.getElementById('evaluationModal'));
        
        // State
        this.isRecording = false;
        this.recognition = null;
        this.synth = window.speechSynthesis;
        this.selectedVoice = null;
        this.questionStartTime = Date.now();
        this.currentQuestionText = this.questionTextElem ? this.questionTextElem.innerText.trim() : "";

        this.initSpeechSynthesis();
        this.initSpeechRecognition();
        this.attachEventListeners();
        
        // Automatically speak the first question on page load
        setTimeout(() => {
            this.speakText(this.currentQuestionText);
        }, 800);
    }

    // 1. Text-to-Speech (AI Voice)
    initSpeechSynthesis() {
        if (!('speechSynthesis' in window)) {
            console.warn("SpeechSynthesis API not supported in this browser.");
            return;
        }

        const loadVoices = () => {
            const voices = this.synth.getVoices();
            // Prefer natural English voices (Google UK/US, Samantha, Microsoft)
            this.selectedVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Online'))) ||
                                 voices.find(v => v.lang.startsWith('en')) || 
                                 voices[0];
        };

        loadVoices();
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = loadVoices;
        }
    }

    speakText(text, onComplete) {
        if (!('speechSynthesis' in window) || !text) {
            if (onComplete) onComplete();
            return;
        }

        // Cancel any pending speech
        this.synth.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        if (this.selectedVoice) {
            utterance.voice = this.selectedVoice;
        }
        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        utterance.onstart = () => {
            if (this.aiSpeakingIndicator) {
                this.aiSpeakingIndicator.classList.remove('d-none');
            }
        };

        utterance.onend = () => {
            if (this.aiSpeakingIndicator) {
                this.aiSpeakingIndicator.classList.add('d-none');
            }
            if (onComplete) onComplete();
        };

        utterance.onerror = (e) => {
            console.error("Speech synthesis error:", e);
            if (this.aiSpeakingIndicator) {
                this.aiSpeakingIndicator.classList.add('d-none');
            }
            if (onComplete) onComplete();
        };

        this.synth.speak(utterance);
    }

    // 2. Speech-to-Text (Candidate Microphone)
    initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            this.updateMicStatus("Microphone not supported in this browser. Please type your answer.", "text-danger");
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';

        this.recognition.onstart = () => {
            this.isRecording = true;
            this.micBtn.classList.remove('btn-outline-danger');
            this.micBtn.classList.add('btn-danger', 'recording-pulse');
            this.updateMicStatus("Listening... Speak your answer now", "text-danger fw-bold");
        };

        this.recognition.onresult = (event) => {
            let fullTranscript = '';
            for (let i = 0; i < event.results.length; i++) {
                fullTranscript += event.results[i][0].transcript + ' ';
            }
            this.transcriptInput.value = fullTranscript.trim();
        };

        this.recognition.onerror = (event) => {
            console.error("Speech recognition error:", event.error);
            this.isRecording = false;
            this.micBtn.classList.remove('btn-danger', 'recording-pulse');
            this.micBtn.classList.add('btn-outline-danger');
            if (event.error === 'not-allowed') {
                this.updateMicStatus("Microphone permission denied. Enable mic in browser or type answer.", "text-danger");
            } else {
                this.updateMicStatus("Mic idle. Click microphone to speak again.", "text-muted");
            }
        };

        this.recognition.onend = () => {
            if (this.isRecording) {
                // Restart if still marked recording
                try { this.recognition.start(); } catch(e){}
            } else {
                this.micBtn.classList.remove('btn-danger', 'recording-pulse');
                this.micBtn.classList.add('btn-outline-danger');
                this.updateMicStatus("Microphone paused. Click to speak.", "text-muted");
            }
        };
    }

    toggleRecording() {
        if (!this.recognition) {
            alert("Web Speech API is not supported in this browser. You can type your answer directly into the text box.");
            return;
        }

        if (this.isRecording) {
            this.isRecording = false;
            this.recognition.stop();
        } else {
            // Stop AI voice if it was speaking
            this.synth.cancel();
            if (this.aiSpeakingIndicator) this.aiSpeakingIndicator.classList.add('d-none');

            try {
                this.recognition.start();
            } catch (err) {
                console.warn("Recognition already active", err);
            }
        }
    }

    updateMicStatus(message, className) {
        if (this.micStatus) {
            this.micStatus.className = `small ${className}`;
            this.micStatus.innerText = message;
        }
    }

    // 3. Submit Candidate Answer to Django Backend
    async submitAnswer() {
        const answerText = this.transcriptInput.value.trim();
        if (!answerText) {
            alert("Please speak or type an answer before submitting.");
            return;
        }

        // Stop microphone and speech
        if (this.isRecording && this.recognition) {
            this.isRecording = false;
            this.recognition.stop();
        }
        this.synth.cancel();

        const timeTakenSeconds = Math.round((Date.now() - this.questionStartTime) / 1000);

        // Show loading state
        this.submitBtn.disabled = true;
        this.submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Evaluating with AI...`;

        try {
            const response = await fetch('/interviews/api/submit-answer/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    question_id: this.currentQuestionId,
                    recognized_text: answerText,
                    time_taken: timeTakenSeconds
                })
            });

            const result = await response.json();
            if (result.status === 'success') {
                this.displayEvaluationModal(result);
            } else {
                alert("Evaluation error: " + (result.message || "Unknown error"));
                this.resetSubmitButton();
            }
        } catch (error) {
            console.error("Submission failed:", error);
            alert("Server connection failed. Please try submitting again.");
            this.resetSubmitButton();
        }
    }

    // 4. Display Evaluation Feedback & Speak Response
    displayEvaluationModal(data) {
        document.getElementById('modalScore').innerText = `${data.score}/10`;
        document.getElementById('modalSpokenFeedback').innerText = data.spoken_feedback;
        document.getElementById('modalImprovedAnswer').innerText = data.improved_answer;

        // Render Strengths
        const strengthsList = document.getElementById('modalStrengths');
        strengthsList.innerHTML = '';
        (data.positive_points || []).forEach(pt => {
            const li = document.createElement('li');
            li.innerHTML = `<i class="fa-solid fa-check-circle text-success me-2"></i>${pt}`;
            strengthsList.appendChild(li);
        });

        // Render Missing / Mistakes
        const missingList = document.getElementById('modalMissing');
        missingList.innerHTML = '';
        (data.missing_concepts || data.mistakes || []).forEach(pt => {
            const li = document.createElement('li');
            li.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-warning me-2"></i>${pt}`;
            missingList.appendChild(li);
        });

        // Configure Next Button in modal
        const nextActionBtn = document.getElementById('modalNextActionBtn');
        if (data.is_finished) {
            nextActionBtn.innerText = "View Final Results & Report";
            nextActionBtn.onclick = () => {
                window.location.href = data.redirect_url;
            };
        } else {
            nextActionBtn.innerText = `Proceed to Question ${data.next_question.number} of ${this.totalQuestions}`;
            nextActionBtn.onclick = () => {
                this.loadNextQuestion(data.next_question);
                this.evaluationModal.hide();
            };
        }

        // Show Modal
        this.evaluationModal.show();

        // Speak the dynamic interviewer feedback aloud!
        this.speakText(data.spoken_feedback);
    }

    loadNextQuestion(nextQuestion) {
        this.currentQuestionId = nextQuestion.id;
        this.currentQuestionNumber = nextQuestion.number;
        this.currentQuestionText = nextQuestion.text;

        this.questionNumberElem.innerText = `Question ${nextQuestion.number} of ${this.totalQuestions}`;
        this.questionTextElem.innerText = nextQuestion.text;

        // Reset answer input & timing
        this.transcriptInput.value = '';
        this.questionStartTime = Date.now();
        this.resetSubmitButton();

        // Update progress bar
        const progressPercent = Math.round(((nextQuestion.number - 1) / this.totalQuestions) * 100);
        const progressBar = document.getElementById('sessionProgressBar');
        if (progressBar) progressBar.style.width = `${progressPercent}%`;

        // Speak the next question aloud automatically
        setTimeout(() => {
            this.speakText(nextQuestion.text);
        }, 500);
    }

    resetSubmitButton() {
        this.submitBtn.disabled = false;
        this.submitBtn.innerHTML = `<i class="fa-solid fa-paper-plane me-1"></i> Submit Answer`;
    }

    attachEventListeners() {
        if (this.micBtn) {
            this.micBtn.addEventListener('click', () => this.toggleRecording());
        }
        if (this.submitBtn) {
            this.submitBtn.addEventListener('click', () => this.submitAnswer());
        }
        if (this.replayQuestionBtn) {
            this.replayQuestionBtn.addEventListener('click', () => {
                this.speakText(this.currentQuestionText);
            });
        }

        const endInterviewBtn = document.getElementById('endInterviewEarlyBtn');
        if (endInterviewBtn) {
            endInterviewBtn.addEventListener('click', async () => {
                if (confirm("Are you sure you want to end the interview early? Your answers so far will be scored.")) {
                    const res = await fetch('/interviews/api/end-interview/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.csrfToken
                        },
                        body: JSON.stringify({ session_id: this.sessionId })
                    });
                    const r = await res.json();
                    if (r.redirect_url) window.location.href = r.redirect_url;
                }
            });
        }
    }
}
