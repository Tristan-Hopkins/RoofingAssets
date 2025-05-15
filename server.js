const express = require('express');
const path = require('path');
const cors = require('cors');
const fs = require('fs');
const app = express();
const port = 3000;

// Enable CORS for all routes
app.use(cors());

// Serve images from the output/images directory
app.use('/RoofingMaterials/Images', express.static(path.join(__dirname, 'output/images')));

// Route to serve the all-companies.json file
app.get('/RoofingMaterials/all-companies.json', (req, res) => {
  const filePath = path.join(__dirname, 'output', 'all-companies.json');
  
  // Check if the file exists
  if (fs.existsSync(filePath)) {
    res.sendFile(filePath);
  } else {
    res.status(404).json({ error: 'all-companies.json file not found' });
  }
});

// Root route with information
app.get('/', (req, res) => {
  res.send(`
    <h1>Roofing Materials Server</h1>
    <p>Server is running successfully!</p>
    <ul>
      <li>Access images at: <a href="/RoofingMaterials/Images">/RoofingMaterials/Images/{filename}</a></li>
      <li>Access companies data at: <a href="/RoofingMaterials/all-companies.json">/RoofingMaterials/all-companies.json</a></li>
    </ul>
  `);
});

// Start the server
app.listen(port, () => {
  console.log(`Roofing Materials Server running at http://localhost:${port}`);
  console.log(`Access images at http://localhost:${port}/RoofingMaterials/Images/{filename}`);
  console.log(`Access companies data at http://localhost:${port}/RoofingMaterials/all-companies.json`);
});
