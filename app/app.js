'use strict';

var fs = require('fs'),
    util = require('util'),
    request = require('request'),
    inspect = require('util').inspect,
    os = require('os'),
    Busboy = require('busboy'),
    express = require('express'),
    app = express(),
    path = require('path'),
    connect = require('connect'),
    bodyParser = require('body-parser'),
    child_process = require('child_process');

var robot_process = null;

var clientId = 'test-app';   
var clientSecret = 'fd069834defd4bdca5f366265b1577ea';
//'ceb21dbbce474431ad3fc95b12a6cc90'; // API key from Bing Speech service
var savedFile = null;

function getAccessToken(clientId, clientSecret, callback) {
  //curl -v -X POST "https://api.cognitive.microsoft.com/sts/v1.0/issueToken" -H "Content-type: application/x-www-form-urlencoded" -H "Content-Length: 0" -H "Ocp-Apim-Subscription-Key: fd069834defd4bdca5f366265b1577ea
  request.post({
    url: 'https://api.cognitive.microsoft.com/sts/v1.0/issueToken',
    headers: {
      'Ocp-Apim-Subscription-Key': clientSecret
    }
  }, function(err, resp, body) {
    if(err) return callback(err);
    try {
      var accessToken = body;
      if(accessToken) {
        callback(null, accessToken);
      } else {
        callback(body);
      }
    } catch(e) {
      callback(e);
    }
  });
}

function speechToText(filename, accessToken, callback) {
  //curl -v -X POST "https://speech.platform.bing.com/speech/recognition/interactive/cognitiveservices/v1?language=en-US&locale=en&format=txt&requestid=your_guid" -H "Transfer-Encoding: chunked" -H 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzY29wZSI6Imh0dHBzOi8vc3BlZWNoLnBsYXRmb3JtLmJpbmcuY29tIiwic3Vic2NyaXB0aW9uLWlkIjoiODYwNmNkMTAwZWExNGVhYzk2Njc0OTYyNTRhZDI1YmIiLCJwcm9kdWN0LWlkIjoiQmluZy5TcGVlY2guRjAiLCJjb2duaXRpdmUtc2VydmljZXMtZW5kcG9pbnQiOiJodHRwczovL2FwaS5jb2duaXRpdmUubWljcm9zb2Z0LmNvbS9pbnRlcm5hbC92MS4wLyIsImF6dXJlLXJlc291cmNlLWlkIjoiL3N1YnNjcmlwdGlvbnMvNzEzMDI3ZGUtYjYzZS00YjYxLWFjYjktZjM1N2VjY2M0MTU5L3Jlc291cmNlR3JvdXBzL0EvcHJvdmlkZXJzL01pY3Jvc29mdC5Db2duaXRpdmVTZXJ2aWNlcy9hY2NvdW50cy9TcGVhY2giLCJpc3MiOiJ1cm46bXMuY29nbml0aXZlc2VydmljZXMiLCJhdWQiOiJ1cm46bXMuc3BlZWNoIiwiZXhwIjoxNTA1NTY3NjY5fQ.be2Sy4JvzuR_LtAVJp5XyVOtTXm_L_YIRqrieD1UEnw' -H 'Content-type: audio/wav; codec="audio/pcm"; samplerate=16000' --data-binary @t.wav
  fs.readFile(filename, function(err, waveData) {
    if(err) return callback(err);
    request.post({
      url: 'https://speech.platform.bing.com/speech/recognition/interactive/cognitiveservices/v1',
      qs: {
        'language': 'en-US',
        'locale': 'en-US',
        'format': 'json',
        'requestid': '1d4b6030-9099-11e0-91e4-0800200c9a66'
      },
      body: waveData,
      headers: {
        'Authorization': 'Bearer ' + accessToken,
        'Content-Type': 'audio/wav; samplerate=16000',
        'Content-Length' : waveData.length
      }
    }, function(err, resp, body) {
      if(err) return callback(err);
      try {
        callback(null, JSON.parse(body));
      } catch(e) {
        callback(e);
      }
    });
  });
}

function LUIS(query, callback) {
    request.get({
      url: 'https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/4c093489-e725-48c6-b675-aa6281bc4cf9',
      qs: {
        'subscription-key': 'a58b814c31ce4c74b7d33e37be1aeea6',
        'q': query,
        'staging': true
      }
    }, function(err, resp, body) {
      if(err) return callback(err);
      try {
        callback(null, JSON.parse(body));
      } catch(e) {
        callback(e);
      }
    });
}

////////////////////////
// Microsoft Emotion API
////////////////////////

const EMOTION_KEY_1 = "bad3ba09148644e5ac20250bd87a6c5a";
const EMOTION_KEY_2 = "b8751f4fff674292a0fca0a8e260fcdb";
const EMOTION_ENDPPINT = "https://westus.api.cognitive.microsoft.com/emotion/v1.0";

////////////////////////
// End Microsoft Emotion API
////////////////////////

app.use(express.static(__dirname + '/public'));
app.use(bodyParser.urlencoded({ extended: true }));

app.get('/', function(req, res) {
  res.sendFile('index.html');
});


function initRobotSubprocess() {
    var child = child_process.spawn('python', ['../robot.py']);
    var logStream = fs.createWriteStream('./robot_subprocess.log', {flags: 'a'});
    child.stdout.pipe(logStream);
    child.stderr.pipe(logStream);

    child.on('error', function (err) {
        console.log('child process error' + err);
    });
    child.on('exit', function (code, signal) {
        console.log('child process exited with code ' + code + ' and signal ' + signal);
    });
    return child;
}

function detectAction(luisRes) {
    var intent = luisRes['topScoringIntent']['intent'];
    if (intent == 'Bring') {
        return 'ShakingHands';
    }
    return 'Excited';
}

function sendActionToRobot(action) {
    console.log('Sending action to robot: ' + action);

    var port = 5000;
    request.get({
        url: 'http://localhost:' + port + '/cmd/' + action,
    }, function(err, resp, body) {
        if(err) {
            console.log('Encountered error when sending action to robot')
        }
    });

}


app.post('/recognize', function(req, res) {

  var busboy = new Busboy({ headers: req.headers });
  busboy.on('file', function(fieldname, file, filename, encoding, mimetype) {
      savedFile = path.join(os.tmpDir(), 'test.wav');
      file.pipe(fs.createWriteStream(savedFile));
      console.log('File is saved to: ' + savedFile);
  });

  busboy.on('finish', function() {
      var result = '';
      getAccessToken(clientId, clientSecret, function(err, accessToken) {
          if(err) return console.log(err);
          console.log('Got access token: ' + accessToken);
          speechToText(savedFile, accessToken, function(err, speechres) {
              if(err) return console.log(err);
              res.status(200).send(String(speechres.DisplayText));
          });
      })

  });

  req.pipe(busboy);
});

app.get('/luis', function(req, res) {
  LUIS(req.query.q, function(err, luisres) {
      if(err) return console.log(err);

        var action = detectAction(luisres);
        sendActionToRobot(action);

        res.status(200).send(luisres);
    });
});

app.listen(process.env.PORT || 3000);
console.log("Running at Port 3000");

robot_process = initRobotSubprocess();