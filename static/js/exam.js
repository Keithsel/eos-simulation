class QuizNode {
    constructor(question, index) {
        this.question = question;
        this.index = index;
        this.next = null;
        this.prev = null;
    }
}

class CircularQuizList {
    constructor(questions) {
        if (!questions || questions.length === 0) {
            throw new Error("Questions array cannot be empty");
        }

        this.head = null;
        this.current = null;
        this.size = questions.length;

        let lastNode = null;
        questions.forEach((question, index) => {
            const node = new QuizNode(question, index);
            if (!this.head) {
                this.head = node;
            } else {
                node.prev = lastNode;
                lastNode.next = node;
            }
            lastNode = node;
        });

        lastNode.next = this.head;
        this.head.prev = lastNode;

        this.current = this.head;
    }

    next() {
        if (!this.current) return null;
        this.current = this.current.next;
        return this.current;
    }

    prev() {
        if (!this.current) return null;
        this.current = this.current.prev;
        return this.current;
    }

    getCurrentIndex() {
        return this.current ? this.current.index : 0;
    }

    getCurrentQuestion() {
        return this.current ? this.current.question : null;
    }

    moveTo(index) {
        let node = this.head;
        for (let i = 0; i < this.size; i++) {
            if (node.index === index) {
                this.current = node;
                return;
            }
            node = node.next;
        }
    }
}


const questions = questionsData;
let quizList;
try {
    quizList = new CircularQuizList(questions);
} catch (e) {
    console.error('Failed to initialize quiz:', e);
    location.href = '/';
}

let answers = new Array(questions.length).fill(null);

if (!window.location.search.includes('token') && quizToken) {
    const newUrl = `${window.location.pathname}?token=${quizToken}`;
    window.history.pushState({}, '', newUrl);
}




function saveProgress() {
    localStorage.setItem(`quiz_${quizToken}`, JSON.stringify({
        answers,
        startTime: new Date().getTime(),
        timeLimit,
        currentIndex: quizList.getCurrentIndex()
    }));
}

function loadProgress() {
    const saved = localStorage.getItem(`quiz_${quizToken}`);
    if (saved) {
        try {
            const data = JSON.parse(saved);
            answers = data.answers || new Array(questions.length).fill(null);
            if (typeof data.currentIndex === 'number') {
                quizList.moveTo(data.currentIndex);
            }
        } catch (error) {
            console.error('Failed to load saved progress:', error);
        }
    }
    updateQuestion();
    updateProgress();
    document.getElementById('answersInput').value = JSON.stringify(answers);
}

function updateQuestion() {
    const question = quizList.getCurrentQuestion();
    const currentQuestion = quizList.getCurrentIndex();

    document.getElementById('selectInfo').textContent =
        `Choose your answer(s) - Select ${question.correct_answers.length} option(s)`;

    const questionTextEl = document.querySelector('.question-text');
    questionTextEl.innerHTML = question.text.replace(/\n/g, '<br>');
    if (question.image_url) {
        questionTextEl.innerHTML += `
          <div class="question-image mt-2">
              <img src="${question.image_url}" alt="Question image" class="img-fluid">
          </div>`;
    }


    const optionsPanel = document.querySelector('.answer-options');
    optionsPanel.innerHTML = question.options
        .map((option, index) => {
            const letter = String.fromCharCode(65 + index);
            return `<div class="form-check"><input class="form-check-input" type="checkbox" name="answer_option" id="option${letter}" value="${letter}"><label class="form-check-label text-nowrap" for="option${letter}">${letter}</label></div>`;
        }).join('');


    const optionsContainer = document.querySelector('.options-text');
    optionsContainer.innerHTML = question.options
        .map((option, index) => {
            const letter = String.fromCharCode(65 + index);
            return option.type === 'image'
                ? `<div class="option-row"><span class="option-letter">${letter}.</span><div class="option-image"><img src="${option.content}" alt="Option ${letter}" class="img-fluid"></div></div>`
                : `<div class="option-row"><span class="option-letter text-nowrap">${letter}. </span><span class="option-content">${option.content.replace(/\n/g, '<br>')}</span></div>`;
        }).join('');


    document.querySelectorAll('input[name="answer_option"]').forEach(cb => cb.checked = false);


    if (answers[currentQuestion]) {
        const savedAnswers = answers[currentQuestion];
        savedAnswers.forEach(answer => {

            const index = question.options.findIndex(opt =>
                JSON.stringify(opt) === JSON.stringify(answer)
            );
            if (index !== -1) {
                const letter = String.fromCharCode(65 + index);
                const checkbox = document.getElementById(`option${letter}`);
                if (checkbox) {
                    checkbox.checked = true;
                }
            }
        });
    }

    document.getElementById('prevBtn').disabled = false;
    optionsPanel.style.height = 'auto';
    optionsPanel.style.maxHeight = '300px';
    optionsPanel.style.minHeight = '200px';
}

function updateProgress() {
    const answered = answers.filter(answer => answer !== null && answer.length > 0).length;
    const progress = (answered / questions.length) * 100;
    document.getElementById('progress-bar').style.width = `${progress}%`;
}

function updateAnswers() {

    const question = quizList.getCurrentQuestion();
    const selectedLetters = Array.from(
        document.querySelectorAll('input[name="answer_option"]:checked')
    ).map(cb => cb.value);

    const selectedAnswers = selectedLetters.map(letter =>
        question.options[letter.charCodeAt(0) - 65]
    );

    answers[quizList.getCurrentIndex()] = selectedAnswers.length > 0 ? selectedAnswers : null;
    document.getElementById('answersInput').value = JSON.stringify(answers);
    saveProgress();
}

document.querySelector('.answer-options').addEventListener('change', updateAnswers);

document.getElementById('prevBtn').addEventListener('click', () => {
    quizList.prev();
    updateProgress();
    updateQuestion();
    saveProgress();
});

document.getElementById('nextBtn').addEventListener('click', () => {
    quizList.next();
    updateProgress();
    updateQuestion();
    saveProgress();
});

document.getElementById('finishCheck').addEventListener('change', (e) => {
    document.getElementById('finishBtn').disabled = !e.target.checked;
});


function calculateRemainingTime() {
    if (!startTime) return timeLimit;
    const start = new Date(startTime);
    const now = new Date();
    const elapsed = Math.floor((now - start) / 1000);
    return Math.max(0, timeLimit - elapsed);
}

function updateTimer() {
    const remaining = calculateRemainingTime();
    const minutes = Math.floor(remaining / 60);
    const seconds = remaining % 60;

    const timeDisplay = document.getElementById('time');
    if (timeDisplay) {
        timeDisplay.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        if (remaining <= 0) {
            document.getElementById('quizForm').submit();
        }
    }
}


document.addEventListener('DOMContentLoaded', () => {
    try {

        updateQuestion();
        updateProgress();


        updateTimer();
        const timerInterval = setInterval(updateTimer, 1000);


        loadProgress();
    } catch (error) {
        console.error('Failed to initialize quiz:', error);
    }
});

document.getElementById('quizForm').addEventListener('submit', () => {
    localStorage.removeItem(`quiz_${quizToken}`);
});

let currentFontSize = 1.3;

function adjustFontSize(delta) {
    currentFontSize = Math.max(0.8, Math.min(1.4, currentFontSize + delta * 0.1));
    document.querySelector('.question-text').style.fontSize = `${currentFontSize * 1.1}rem`;
    document.querySelector('.options-text').style.fontSize = `${currentFontSize}rem`;


    document.querySelectorAll('.option-letter').forEach(el => {
        el.style.fontSize = `${currentFontSize * 1.1}rem`;
    });
    document.querySelectorAll('.option-content').forEach(el => {
        el.style.fontSize = `${currentFontSize}rem`;
    });
}