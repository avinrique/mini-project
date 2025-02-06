import express from 'express';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import bodyParser from 'body-parser';
import axios from 'axios';
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
import path from 'path';
const app = express();
const port = 3001;

// Set EJS as templating engine
app.set('view engine', 'ejs');+
app.set('views', join(__dirname, 'views'));
app.use('/reports', express.static(path.join(__dirname, 'reports')));
// Middleware
app.use(express.static('public'));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Routes
app.get('/', (req, res) => {
  res.render('editor');
});

// Execute code endpoint
app.post('/execute', async (req, res) => {
  const { code, language } = req.body;

  // Map language input to Judge0's language IDs
  const languageIds = {
    javascript: 63,
    python: 71,
    c: 75,
    cpp: 76,
    java: 62,
    // Add more mappings as needed
  };

  const languageId = languageIds[language.toLowerCase()];

  if (!languageId) {
    return res.status(400).json({ error: 'Unsupported language' });
  }

  try {
    
    const response = await axios.post('http://localhost:2358/submissions?wait=true', {
      source_code: code,
      language_id: languageId,
      stdin: null,
    });

    const { stdout, stderr, compile_output, message } = response.data;

    res.json({
      output: stdout || compile_output || message || 'No output',
      error: stderr || null,
    });
  } catch (err) {
    res.status(500).json({
      error: 'Error communicating with Judge0',
      details: err.message,
    });
  }
});


// Linting endpoint
// app.post('/checklint', (req, res) => {
//   const { code, language } = req.body;
//   console.log(code , language)
  
//   // Example linting comments - replace with your actual linting logic
//   const lintingComments = [
//     { line: 1, message: "Missing semicolon", type: "warning" },
//     { line: 3, message: "Unused variable", type: "error" }
//   ];
  
//   res.json({ comments: lintingComments });
// });
app.post('/checklint', async (req, res) => {
  const { code, language } = req.body;

  try {
    // Send the code to Flask server for linting
    const flaskResponse = await axios.post('http://localhost:5000/analyze', {
      code: code
    });

    // Assuming Flask returns linting comments
    const lintingComments = flaskResponse.data.analysis_result || [];
    console.log(lintingComments)

    res.json({ comments: lintingComments });
  } catch (error) {
    console.error('Error checking code linting:', error);
    res.status(500).json({ comments: [], error: 'Failed to check code on Flask server' });
  }
});

app.post('/generate-report', async (req, res) => {
    const { code } = req.body;

    try {
        // Step 1: Analyze code
        const analyzeResponse = await axios.post('http://localhost:5000/analyze', { code });
        const lintingComments = analyzeResponse.data.analysis_result || "No issues found";

        // Step 2: Request Report PDF Generation
        const reportResponse = await axios.post('http://localhost:5000/report', { code, code_sum: lintingComments });
        const lss = `http://localhost:3001/${reportResponse.data.report_location}`
        const pathss = lss.replace(/\\/g, '/');

        console.log( pathss );
        if (reportResponse.data.report_location) {
            res.json({ 
                message: "Report generated", 
                download_url: pathss
            });
        } else {
            res.status(500).json({ error: "Failed to generate report" });
        }
        
    } catch (error) {
        console.error('Error generating report:', error);
        res.status(500).json({ error: 'Error generating report' });
    }
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});