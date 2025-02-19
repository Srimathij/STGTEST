
/* module for importing other js files */
function include(file) {
    const script = document.createElement('script');
    script.src = file;
    script.type = 'text/javascript';
    script.defer = true;
  
    document.getElementsByTagName('head').item(0).appendChild(script);
  }
  
  
  // Bot pop-up intro
  document.addEventListener("DOMContentLoaded", () => {
    const elemsTap = document.querySelector(".tap-target");
    // eslint-disable-next-line no-undef
    const instancesTap = M.TapTarget.init(elemsTap, {});
    instancesTap.open();
    setTimeout(() => {
      instancesTap.close();
    }, 4000);
  });
  
  /* import components */
  include('./static/js/components/index.js');
  
  window.addEventListener('load', () => {
    // initialization
    $(document).ready(() => {
      // Bot pop-up intro
      $("div").removeClass("tap-target-origin");
  
      // drop down menu for close, restart conversation & clear the chats.
      $(".dropdown-trigger").dropdown();
  
      // initiate the modal for displaying the charts,
      // if you dont have charts, then you comment the below line
      $(".modal").modal();
  
      // enable this if u have configured the bot to start the conversation.
      // showBotTyping();
      // $("#userInput").prop('disabled', true);
  
      // if you want the bot to start the conversation
      // customActionTrigger();
      
    });
  
    // Toggle the chatbot screen
    $("#profile_div").click(() => {
      $(".profile_div").toggle();
      $(".widget").toggle();
    });
  
    // clear function to clear the chat contents of the widget.
    $("#clear").click(() => {
      $(".chats").fadeOut("normal", () => {
        $(".chats").html("");
        $(".chats").fadeIn();
      });
    });
  
    // close function to close the widget.
    $("#close").click(() => {
      $(".profile_div").toggle();
      $(".widget").toggle();
      scrollToBottomOfResults();
    });
  });
  
  document. getElementById("sendButton"). onclick = function() {
    sendGreeting();
  
  };
  
  
  // $("#sendButton").click(() => {
  //   // alert('333');
  //   sendGreeting();
  // });
  
  
  $("#voiceButton").click(() => {
    start1();
  });
  
    var val1;
    var reg;
    var speech;
  
    function start1()
    {
      reg = window.SpeechRecognition || window.webkitSpeechRecognition;
      speech = new reg();
  
      speech.onstart = function() {
          console.log("We are listening. Try speaking into the microphone.");
      };
  
      speech.onspeechend = function() {
            // when user is done speaking
            console.log('stop.....')
            speech.stop();
        }
                      
      speech.onresult= function (e)
      {
        $("#userInput").val(e.results[e.resultIndex][0].transcript); 
        console.log(e)
    
          const myTimeout = setTimeout(voiceGreeting, 1000);
      }
      speech.start();
  
    }
  
    function demoval(){
  
      // $("#sendButton").on("click", (e) => {
        const text = $(".usrInput").val();
        if (text === "" || $.trim(text) === "") {
           // e.preventDefault();
            return false;
        }
        // destroy the existing chart
        if (typeof chatChart !== "undefined") {
            chatChart.destroy();
        }
  
        $(".chart-container").remove();
        if (typeof modalChart !== "undefined") {
            modalChart.destroy();
        }
  
        $(".suggestions").remove();
        $("#paginated_cards").remove();
        $(".quickReplies").remove();
        $(".usrInput").blur();
        $(".dropDownMsg").remove();
        setUserResponse(text);
        send(text);
        //e.preventDefault();
        return false;
      // });
    }
  
  
    $(document).ready(function () {
      // Define the chatbot widget element
      var chatbotWidget = $(".widget");
    
      // Define the "Enlarge" button element
      var enlargeButton = $("#enlarge");
    
      // Toggle the enlarged state when the "Enlarge" option is clicked
      enlargeButton.on("click", function () {
        chatbotWidget.toggleClass("enlarged");
      });
    });
    
    function voiceGreeting() 
      {
      //  document.getElementById("sendButton").click();
       demoval();
  
        
        // sendGreeting();
        // $("#sendButton").click(() => {
        //   // alert('333');
        //   // sendGreeting();
        // });
  
  
        // $('#voiceButton').trigger('click');
        // $('#sendButton').trigger('click');
        // $('#userInput').trigger('click');
        // $("#voiceButton").on("click")  
  
        setTimeout( function() 
        {
          
          let responseData = sharedata.data1;
          console.log('---',responseData);
  
          for (var i = 0; i < responseData.length; i++) 
          {
            var botmsgTex = responseData[i].text;
            console.log('voice1: ',botmsgTex)
            // console.log("botmsgTex: "+botmsgTex)
            const msg = new SpeechSynthesisUtterance(botmsgTex);
            window.speechSynthesis.speak(msg);
          }
  
        },4000);
      }
  
      // send button
      function sendGreeting() 
      {
  
        setTimeout( function() 
        {
          
          let responseData = sharedata.data1;
          console.log('---',responseData);
  
          for (var i = 0; i < responseData.length; i++) 
          {
            var botmsgTex = responseData[i].text;
            console.log('send2: ',botmsgTex)
            // console.log("botmsgTex: "+botmsgTex)
            // alert("botmsgTex: " + botmsgTex);
            const msg = new SpeechSynthesisUtterance(botmsgTex);
            window.speechSynthesis.speak(msg);
          }
  
        },4000);
      }
      
      
      document.addEventListener("DOMContentLoaded", () => {
        const uploadButton = document.getElementById('uploadButton');
        const uploadFileInput = document.getElementById('uploadFileInput');
  
        uploadButton.addEventListener('click', () => {
            uploadFileInput.click();
        });
  
        uploadFileInput.addEventListener('change', async (event) => {
            const files = event.target.files;
            if (files.length > 0) {
                const file = files[0];
                displayUploadedFile(file);
                await sendFileToRasa(file);
            }
        });
    });
  
    async function sendFileToRasa(file) {
        const formData = new FormData();
        formData.append('file', file);
  
        try {
            const response = await axios.post('/webhooks/rest/webhook', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });
  
            const messages = response.data;
            messages.forEach(message => {
                displayMessage(message.text);
            });
        } catch (error) {
            console.error('Error sending file to Rasa:', error);
        }
    }
  
    function displayUploadedFile(file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const fileUrl = e.target.result;
            const fileElement = document.createElement('div');
            fileElement.className = 'uploaded-file';
            fileElement.innerHTML = `
                <p>Uploaded file:</p>
                <img src="${fileUrl}" alt="${file.name}" class="uploaded-image"/>
            `;
  
            const chatWindow = document.querySelector('.chats');
            chatWindow.appendChild(fileElement);
            chatWindow.scrollTop = chatWindow.scrollHeight;
        };
        reader.readAsDataURL(file);
    }
  
    function displayMessage(message) {
        const chatWindow = document.querySelector('.chats');
        const messageElement = document.createElement('div');
        messageElement.textContent = message;
        chatWindow.appendChild(messageElement);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
      