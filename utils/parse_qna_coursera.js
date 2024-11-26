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

    // Clean text helper
    const cleanText = (text) => text.replace(/"/g, "'").trim();

    // Extract data from each question block
    const quizData = [];
    questionBlocks.forEach(block => {
        // Extract the question text and image
        const questionElement = block.querySelector(".css-1474zrz");
        const questionText = questionElement ? cleanText(questionElement.innerText) : null;

        // Get question image from within the question prompt area only
        const questionPrompt = block.querySelector('[id^="prompt-autoGradableResponseId"]');
        const questionImage = questionPrompt ? questionPrompt.querySelector("img") : null;
        const questionImageUrl = questionImage ? questionImage.src : null;

        // Extract options and the correct answer
        const options = [];
        let correctAnswer = null;
        const labels = block.querySelectorAll("label");
        labels.forEach(label => {
            // Extract option text and image
            const optionText = cleanText(label.innerText);
            const optionImage = label.querySelector("img");
            const optionImageUrl = optionImage ? optionImage.src : null;
            
            // Only use the image URL if it's an image-only option
            const finalOptionText = optionText.trim() === '' ? optionImageUrl : optionText;
            options.push(finalOptionText);

            // Check if this option is marked as correct
            const input = label.querySelector("input[type='radio']");
            if (input && input.checked) {
                correctAnswer = finalOptionText;
            }
        });

        // Append question data if valid
        if (questionText && options.length > 0) {
            quizData.push({
                question: questionImageUrl ? `${questionText} [Image: ${questionImageUrl}]` : questionText,
                options: options,
                correct_answer: correctAnswer ? [correctAnswer] : []
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
