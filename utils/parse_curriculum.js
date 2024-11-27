(() => {
    // Helper to clean and extract text from span by ID
    const getSpanText = (id) => {
        const span = document.getElementById(id);
        return span ? span.textContent.trim() : '';
    };

    // Extract curriculum header info
    const getCurriculumInfo = () => {
        // Get the curriculum name from the table instead of profile
        const nameElement = document.querySelector('#lblName');
        return {
            code: getSpanText('txtCurriculumCode'),
            name: nameElement ? nameElement.textContent.split('(')[0].trim() : '',
            englishName: getSpanText('lblEnglishName'),
        };
    };

    // Process subject name to split English/Vietnamese parts
    const processSubjectName = (fullName) => {
        // Replace escaped newlines with spaces first
        fullName = fullName.replace(/\n/g, ' ');
        
        const names = {
            full: fullName
        };

        if (fullName.includes('_')) {
            const [enPart, viPart] = fullName.split('_');
            names.en = enPart.trim();
            names.vi = viPart.trim();
        } else {
            names.vi = fullName.trim();
            names.en = null;
        }

        return names;
    };

    // Process prerequisite string into structured format
    const processPrerequisite = (prereqStr) => {
        if (!prereqStr || prereqStr === 'None' || prereqStr === 'Không') {
            return {
                required: false,
                logic: null,
                raw: prereqStr || null
            };
        }

        // Handle nested conditions
        const parseCondition = (str) => {
            // Remove outer parentheses if they exist
            str = str.trim().replace(/^\((.*)\)$/, '$1');

            if (str.includes(' and ')) {
                return {
                    operator: 'AND',
                    requirements: str.split(' and ').map(s => parseCondition(s.trim()))
                };
            } else if (str.includes(' or ')) {
                return {
                    operator: 'OR',
                    requirements: str.split(' or ').map(s => parseCondition(s.trim()))
                };
            } else {
                return {
                    operator: 'SINGLE',
                    code: str.trim()
                };
            }
        };

        return {
            required: true,
            logic: parseCondition(prereqStr),
            raw: prereqStr
        };
    };

    // Extract total subjects and credits
    const getTotalCount = () => {
        const text = getSpanText('lblTotalCredit');
        const [subjects, credits] = text.match(/\d+/g);
        return {
            totalSubjects: parseInt(subjects),
            totalCredits: parseInt(credits)
        };
    };

    // Extract curriculum detail table
    const getCurriculumDetail = () => {
        const table = document.getElementById('gvSubs');
        if (!table) return [];

        const rows = Array.from(table.querySelectorAll('tr')).slice(1); // Skip header
        return rows.map(row => {
            const cells = row.querySelectorAll('td');
            const code = cells[0].textContent.trim();
            const name = cells[1].textContent.trim();
            
            return {
                code: code,
                name: processSubjectName(name),
                credits: parseInt(cells[3].textContent.trim()),
                semester: parseInt(cells[2].textContent.trim()),
                prerequisites: processPrerequisite(cells[4].textContent.trim())
            };
        });
    };

    // Combine all data with consistent structure
    const curriculumData = {
        metadata: {
            code: getSpanText('txtCurriculumCode'),
            name: {
                vi: getCurriculumInfo().name,
                en: getSpanText('lblEnglishName')
            },
            totals: getTotalCount()
        },
        subjects: getCurriculumDetail()
    };

    // Download as JSON with curriculum code as filename
    const file = new Blob([JSON.stringify(curriculumData, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(file);
    a.download = `${curriculumData.metadata.code}.json`;
    a.click();

    console.log('Curriculum data extracted:', curriculumData);
})();
