(() => {
    // Locate the container for all questions
    const quizContainer = document.querySelector(".css-1h9exxh");
    if (!quizContainer) {
        console.error("Quiz container not found.");
        return;
    }

    // Locate all question blocks
    const questionBlocks = quizContainer.querySelectorAll(".css-dqaucz");
    if (questionBlocks.length === 0) {
        console.error("No question blocks found.");
        return;
    }

    // Clean text helper - handle escapes and normalize whitespace
    const cleanText = (text) => {
        return text
            .replace(/"/g, "'")
            .replace(/\n/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    };

    // Process content that might have text and/or image
    const processContent = (element) => {
        if (!element) return null;

        const text = cleanText(element.innerText);
        // Get question image from within the question prompt area only
        const questionPrompt = element.closest('.css-dqaucz').querySelector('[id^="prompt-autoGradableResponseId"]');
        const img = questionPrompt ? questionPrompt.querySelector('img') : null;
        const imageUrl = img ? img.src : null;

        return imageUrl ? `${text} [Image: ${imageUrl}]` : text;
    };

    // Process an option element
    const processOption = (label) => {
        const text = cleanText(label.innerText);
        const img = label.querySelector('img');
        const imageUrl = img ? img.src : null;
        const input = label.querySelector('input[type="radio"], input[type="checkbox"]');

        return {
            text: text.trim() === '' ? imageUrl : text,
            isSelected: input ? input.checked : false
        };
    };

    // Extract data from each question block
    const quizData = [];
    questionBlocks.forEach(block => {
        // Process question content
        const questionElement = block.querySelector('.css-1474zrz');
        const questionText = questionElement ? cleanText(questionElement.innerText) : null;
        
        // Get question image specifically from the prompt area
        const questionPrompt = block.querySelector('[id^="prompt-autoGradableResponseId"]');
        const questionImage = questionPrompt ? questionPrompt.querySelector('img') : null;
        const questionImageUrl = questionImage ? questionImage.src : null;

        // Process options and answers
        const options = [];
        const correctAnswer = [];
        
        block.querySelectorAll('label').forEach(label => {
            const option = processOption(label);
            options.push(option.text);
            if (option.isSelected) {
                correctAnswer.push(option.text);
            }
        });

        // Append question data if valid (matching original format)
        if (questionText && options.length > 0) {
            quizData.push({
                question: questionImageUrl ? `${questionText} [Image: ${questionImageUrl}]` : questionText,
                choices: options,
                correct_answer: correctAnswer
            });
        }
    });

    // Download as JSON
    const file = new Blob([JSON.stringify(quizData, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(file);
    a.download = "quiz_data.json";
    a.click();

    console.log("Extracted Quiz Data:", quizData);
})();
