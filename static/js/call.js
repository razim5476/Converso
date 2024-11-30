'use strict';

const baseURL = "/";
let localVideo = document.querySelector('#localVideo');
let remoteVideo = document.querySelector('#remoteVideo');
let otherUser, remoteRTCMessage, peerConnection, remoteStream, localStream;
let iceCandidatesFromCaller = [];
let callInProgress = false;

// WebSocket connection for signaling
let callSocket;
function connectSocket(username) {
    const wsScheme = window.location.protocol === "https:" ? "wss://" : "ws://";
    callSocket = new WebSocket(`${wsScheme}${window.location.host}/ws/call/`);

    callSocket.onopen = () => {
        callSocket.send(JSON.stringify({
            type: 'login',
            data: { name: username }
        }));
    };

    callSocket.onmessage = (e) => {
        const response = JSON.parse(e.data);
        const type = response.type;

        if (type === 'call_received') {
            onNewCall(response.data);
        } else if (type === 'call_answered') {
            onCallAnswered(response.data);
        } else if (type === 'ICEcandidate') {
            onICECandidate(response.data);
        }
    };
}

// Handle incoming call
function onNewCall(data) {
    otherUser = data.caller;
    remoteRTCMessage = data.rtcMessage;
    document.getElementById("callerName").innerText = otherUser;
    document.getElementById("answer").style.display = "block";
}

// Handle accepted call
function onCallAnswered(data) {
    remoteRTCMessage = data.rtcMessage;
    peerConnection.setRemoteDescription(new RTCSessionDescription(remoteRTCMessage));
    document.getElementById("calling").style.display = "none";
    callProgress();
}

// Handle ICE Candidate
function onICECandidate(data) {
    const candidate = new RTCIceCandidate({
        sdpMLineIndex: data.rtcMessage.label,
        candidate: data.rtcMessage.candidate
    });

    if (peerConnection) {
        peerConnection.addIceCandidate(candidate).catch(console.error);
    } else {
        iceCandidatesFromCaller.push(candidate);
    }
}

// Initiate call
function call() {
    const userToCall = document.getElementById("callName").value;
    if (!userToCall) return alert("Enter a username to call.");

    otherUser = userToCall;
    beReady().then(() => processCall(userToCall));
}

// Answer call
function answer() {
    beReady().then(processAccept);
}

// Media setup
function beReady() {
    return navigator.mediaDevices.getUserMedia({ audio: true, video: true })
        .then((stream) => {
            localStream = stream;
            localVideo.srcObject = stream;
            return createConnection();
        })
        .catch(console.error);
}

// Create connection
function createConnection() {
    peerConnection = new RTCPeerConnection({
        iceServers: [
            { urls: "stun:stun.l.google.com:19302" },
            {
                urls: "turn:turn.example.com",
                username: "guest",
                credential: "guestpassword"
            }
        ]
    });

    peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
            callSocket.send(JSON.stringify({
                type: 'ICEcandidate',
                data: {
                    user: otherUser,
                    rtcMessage: {
                        label: event.candidate.sdpMLineIndex,
                        candidate: event.candidate.candidate
                    }
                }
            }));
        }
    };

    peerConnection.ontrack = (event) => {
        if (!remoteStream) {
            remoteStream = new MediaStream();
            remoteVideo.srcObject = remoteStream;
        }
        remoteStream.addTrack(event.track);
    };

    localStream.getTracks().forEach((track) => {
        peerConnection.addTrack(track, localStream);
    });
}

// Process call
function processCall(userName) {
    peerConnection.createOffer().then((offer) => {
        peerConnection.setLocalDescription(offer);
        callSocket.send(JSON.stringify({
            type: 'call',
            data: { name: userName, rtcMessage: offer }
        }));
    }).catch(console.error);
}

// Accept call
function processAccept() {
    peerConnection.setRemoteDescription(new RTCSessionDescription(remoteRTCMessage))
        .then(() => peerConnection.createAnswer())
        .then((answer) => {
            peerConnection.setLocalDescription(answer);
            callSocket.send(JSON.stringify({
                type: 'answer_call',
                data: { caller: otherUser, rtcMessage: answer }
            }));
        }).catch(console.error);
}

// Call progress
function callProgress() {
    document.getElementById("videos").style.display = "block";
    document.getElementById("inCall").style.display = "block";
    document.getElementById("otherUserNameC").innerText = otherUser;
    callInProgress = true;
}
