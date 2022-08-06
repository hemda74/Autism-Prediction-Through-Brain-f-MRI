const express = require('express');
const path = require('path');
const axios = require('axios');
const multer = require("multer");
const PORT = 3000;
// express app
const app = express();

// middleware & static files
app.use(express.static('public'));
app.use(express.json())

const storage = multer.diskStorage({
    destination: function(req, file, cb) {
        cb(null, './uploads/');
    },

    // By default, multer removes file extensions so let's add them back
    filename: function(req, file, cb) {
        cb(null, file.originalname);
    }
});

// sendFile will go here
app.get('/', function(req, res) {
  res.sendFile(path.join(__dirname, 'public/html/home.html'));
});

app.get('/about/', function(req, res) {
    res.sendFile(path.join(__dirname, 'public/html/about.html'));
});

app.get('/detection/', function(req, res) {
    res.sendFile(path.join(__dirname, 'public/html/detection.html'));
});

app.get('/team/', function(req, res) {
    res.sendFile(path.join(__dirname, 'public/html/team.html'));
});

app.get('/contact/', function(req, res) {
    res.sendFile(path.join(__dirname, 'public/html/contact.html'));
});

// post fn to receive file from js (multer)
// send the file to the backend in a post request (axios)
// /upload/

app.post('/upload/', function(req, res) {
     
     let upload = multer({ storage: storage }).single('file');
    
     upload(req, res, function(err) {
 
         if (req.fileValidationError) {
             return res.send(req.fileValidationError);
         }
         else if (!req.file) {
             return res.send('Please select a MRI scan to upload');
         }
         else if (err instanceof multer.MulterError) {
             return res.send(err);
         }
         else if (err) {
             return res.send(err);
         }
         model_type = res.req.body.model_type;
         file_Name = res.req.file.filename;
         // call to python backend api --> /diagnose/
        axios({
            method: 'post',
            url: 'http://127.0.0.1:5000/diagnose/',
            data: {'file_name':file_Name, 'model_type':model_type},
            headers: {'content-type':'application/json'}
        }).then(function(out) {
            //  the classification
            // console.log("sucess");
            console.log(out.data);
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.write(JSON.stringify(out.data));
            res.end();
        }).catch(function(error) {
            console.log(error);
        });
     });
});

// 404 page
app.use((req, res) => {
    res.end("Error!")
});

app.listen(PORT, function(err){
    if (err) console.log("Error in server setup")
    console.log("Server listening on Port", PORT);
})