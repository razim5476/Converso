async function startCall(token, uid) {
    client = AgoraRTC.createClient({ mode: "rtc", codec: "vp8" });

    client.on("user-published", async (user, mediaType) => {
        try {
            await client.subscribe(user, mediaType);
            
            if (mediaType === "video") {
                const player = document.createElement("div");
                player.id = `user-${user.uid}`;
                player.style.width = "100%";
                player.style.height = "100%";
                document.getElementById("remote-streams").append(player);
                user.videoTrack.play(`user-${user.uid}`);
            }

            if (mediaType === "audio") {
                user.audioTrack.play();
            }
        } catch (error) {
            console.error("Error publishing remote user:", error);
        }
    });

    client.on("user-unpublished", (user) => {
        const player = document.getElementById(`user-${user.uid}`);
        if (player) player.remove();
    });

    try {
        await client.join(agoraAppId, channelName, token, uid);
        localTracks = await AgoraRTC.createMicrophoneAndCameraTracks();
        
        const [audioTrack, videoTrack] = localTracks;
        const localPlayer = document.createElement("div");
        localPlayer.id = `user-${uid}`;
        document.getElementById("local-stream").append(localPlayer);
        
        videoTrack.play(`user-${uid}`);
        await client.publish([audioTrack, videoTrack]);
    } catch (error) {
        console.error("Error joining or publishing:", error);
    }
}
