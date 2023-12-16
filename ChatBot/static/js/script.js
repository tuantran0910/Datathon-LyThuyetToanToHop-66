const textarea = document.getElementById("userinput");
textarea.addEventListener("input", () => {
    textarea.style.height = "auto";
    textarea.style.height = textarea.scrollHeight + "px";
});

// for scrolling messages
/*function scrollToBottom() {
var div = document.getElementById("upperid");
div.scrollTop = div.scrollHeight;
}*/
function scrollToBottom() {
    textarea.scrollTop = textarea.scrollHeight;
}
scrollToBottom();

// for submiting form
document
    .getElementById("userinputform")
    .addEventListener("submit", function (event) {
        event.preventDefault();
        formsubmitted();
    });

// for suggestions
function onclickSuggestion(message) {
    let userinput = document.getElementById("userinput");
    userinput.value = message;
    formsubmitted();
    document.querySelector(".suggestions").remove();
}

// for upload file
var uploadedFiles = [];
function uploadFile() {
    // Only allow one file to be uploaded
    if (uploadedFiles.length > 0) {
        alert("Only one file can be uploaded");
        return;
    }

    const input = document.createElement("input");
    input.type = "file";
    input.accept = "image/png, image/jpeg, image/jpg";
    input.onchange = function (event) {
        const file = event.target.files[0];

        if (file) {
            if (file.size <= 5 * 1024 * 1024) {
                // Append to uploadedFiles
                uploadedFiles.push(file);

                // Get the inputarea div
                const inputareaDiv = document.getElementById("inputarea");

                if (
                    document.getElementsByClassName("attachmentList").length == 0
                ) {
                    console.log("Not exist attachment list");
                    // Create the attachment list div
                    const attachmentListDiv = document.createElement("div");
                    attachmentListDiv.classList.add("attachmentList");
                    inputareaDiv.appendChild(attachmentListDiv);
                }

                // Get the attachment list div
                const attachmentListDiv =
                    document.getElementsByClassName("attachmentList")[0];

                // Create the attachment div
                const attachmentDiv = document.createElement("div");
                attachmentDiv.className = "attachmentsection";
                attachmentListDiv.appendChild(attachmentDiv);

                // Create the attachment content
                const attachmentcontent = document.createElement("div");
                attachmentcontent.textContent = `${file.name} (${file.size})`;
                attachmentcontent.className = "attachmentcontent";
                attachmentDiv.appendChild(attachmentcontent);

                // Create the attachment cancel button
                const attachmentcancel = document.createElement("button");
                attachmentcancel.textContent = "X";
                attachmentcancel.className = "attachmentcancel";
                attachmentcancel.type = "button";
                attachmentcancel.onclick = function (event) {
                    deleteAttachment(event);
                };
                attachmentDiv.appendChild(attachmentcancel);
            } else {
                alert("File size must be less than 5MB");
            }
        } else {
            alert("File not available");
        }
    };
    input.click();
}

// Delete attachment
function deleteAttachment(event) {
    const attachmentDiv = event.target.parentNode;
    const attachmentListDiv = attachmentDiv.parentNode;
    attachmentListDiv.removeChild(attachmentDiv);

    // Remove from uploadedFiles
    const attachmentcontent =
        attachmentDiv.getElementsByClassName("attachmentcontent")[0];
    const fileName = attachmentcontent.textContent.split(" ")[0];
    const fileIndex = uploadedFiles.findIndex(
        (file) => file.name === fileName
    );
    uploadedFiles.splice(fileIndex, 1);
}

function deleteAttachmentSection() {
    const attachmentListDiv =
        document.getElementsByClassName("attachmentList")[0];
    attachmentListDiv.parentNode.removeChild(attachmentListDiv);
}

// sending request to python server
const formsubmitted = async () => {
    let userinput = document.getElementById("userinput").value;
    let sendbtn = document.getElementById("sendbtn");
    let userinputarea = document.getElementById("userinput");
    let upperdiv = document.getElementById("upperid");

    // Check if userinput is empty and uploadedFiles is empty
    if (userinput.trim() === "" && uploadedFiles.length === 0) {
        return;
    }

    sendbtn.disabled = true;
    userinputarea.disabled = true;
    document.getElementById("userinput").value = "";
    document.getElementById("userinput").placeholder = "Wait . . .";

    if (document.getElementsByClassName("attachmentList").length > 0) {
        deleteAttachmentSection();
    }

    if (uploadedFiles.length > 0) {
        console.log("Uploaded files: ", uploadedFiles);
        const image = uploadedFiles[0];
        const reader = new FileReader();
        reader.onload = function (event) {
            upperdiv.innerHTML =
                upperdiv.innerHTML +
                `
        <div class="message">
        <div class="usermessagediv flex flex-col">
            <div class="usermessage">
            <div>${userinput}</div>
            <img src="${event.target.result}" width="200" class="uploadimg"/>
            </div>
        </div>
        </div>
    `;
        };
        reader.readAsDataURL(image);

        // Send image to server
        const formData = new FormData();
        formData.append("fileInput", image);
        let userinput = document.getElementById("userinput").value;
        let sendbtn = document.getElementById("sendbtn");
        const image_response = await fetch("http://127.0.0.1:5000/upload", {
            method: "POST",
            body: formData,
        });

        let image_response_json = await image_response.json();
        if (!image_response_json.response) {
            console.error("!Error uploading image");
        }
    } else {
        upperdiv.innerHTML =
            upperdiv.innerHTML +
            `<div class="message">
        <div class="usermessagediv">
                <div class="usermessage">
                    <div>${userinput}</div>
                </div>
        </div>
    </div>`;
    }

    if (userinput.trim() === "") {
        document.getElementById("userinput").placeholder = "Your message...";
        sendbtn.disabled = false;
        userinputarea.disabled = false;
        uploadedFiles = [];
        scrollToBottom();
        return;
    }

    uploadedFiles = [];
    scrollToBottom();
    const message_response = await fetch("http://127.0.0.1:5000/data", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ data: userinput }),
    });

    let message_response_json = await message_response.json();
    document.getElementById("userinput").placeholder = "Your message...";
    if (message_response_json.response) {
        let message = message_response_json.message;
        let imgs = message_response_json.imgs;
        let message_list = message_response_json.list;

        if (message_list) {
            insertImages(imgs, message);
        } else {
            message = message.toString();
            upperdiv.innerHTML =
                upperdiv.innerHTML +
                `<div class="message">
                    <div class="appmessagediv">
                        <div class="appmessage" id="temp">

                        </div>
                    </div>
                </div>`;
            let temp = document.getElementById("temp");
            let index = 0;
            function displayNextLetter() {
                scrollToBottom();
                if (index < message.length) {
                    temp.innerHTML = temp.innerHTML + message[index];
                    index++;
                    setTimeout(displayNextLetter, 30);
                } else {
                    temp.removeAttribute("id");
                    sendbtn.disabled = false;
                    userinputarea.disabled = false;
                }
            }
            displayNextLetter();
        }
        scrollToBottom();
    } else {
        let message = message_response_json.message;
        upperdiv.innerHTML =
            upperdiv.innerHTML +
            `<div class="message">
        <div class="appmessagediv">
            <div class="appmessage"  style="border: 1px solid red;">
                ${message}
            </div>
        </div>
    </div>`;
        sendbtn.disabled = false;
        userinputarea.disabled = false;
    }
    scrollToBottom();
};

// Insert images
const insertImages = async (urls, message = null) => {
    let upperdiv = document.getElementById("upperid");
    let sendbtn = document.getElementById("sendbtn");
    let userinputarea = document.getElementById("userinput");
    sendbtn.disabled = true;
    userinputarea.disabled = true;
    console.log("Urls: ", urls);
    upperdiv.innerHTML =
        upperdiv.innerHTML +
        `<div class="message">
                <div class="chatbotheader">
                    <img src="https://psc2.cf2.poecdn.net/e624182724b2f7d087d86e14094be569c56fc207/_next/static/media/assistant.b077c338.svg" alt="chatbotheader" class="chatbotheaderimage" />
                    <div class="chatbotheadername">Tuan Dep Trai</div>
                </div>
                <div class="appmessagediv">
                    <div class="appmessage" id="temp">
                    </div>
                </div>
            </div>`;
    let temp = document.getElementById("temp");

    if (message) {
        let message_div = document.createElement("div");
        message_div.textContent = message;
        message_div.style.marginBottom = "10px";
        temp.appendChild(message_div);
    }

    // Loop through urls
    for (let i = 0; i < urls.length; i++) {
        // Sleep for 0.5s
        await new Promise((resolve) => setTimeout(resolve, 500));
        let img = new Image();
        img.src = "data:image/png;base64," + urls[i];
        img.width = 200;
        temp.appendChild(img);
        scrollToBottom();
    }
    temp.removeAttribute("id");
    sendbtn.disabled = false;
    userinputarea.disabled = false;

    /*
    const formData = new FormData();
    formData.append("urls", JSON.stringify(urls));
    // Send relative path to server
    let image_response = await fetch("http://127.0.0.1:5000/getcloth", {
        method: "POST",
        body: formData,
    });

    let image_response_json = await image_response.json();
    if (image_response_json.response) {
        // Get images
        let imgs = image_response_json.imgs;
        upperdiv.innerHTML =
            upperdiv.innerHTML +
            `<div class="message">
                <div class="chatbotheader">
                    <img src="https://psc2.cf2.poecdn.net/e624182724b2f7d087d86e14094be569c56fc207/_next/static/media/assistant.b077c338.svg" alt="chatbotheader" class="chatbotheaderimage" />
                    <div class="chatbotheadername">Tuan Dep Trai</div>
                </div>
                <div class="appmessagediv">
                    <div class="appmessage" id="temp">
                    </div>
                </div>
            </div>`;
        let temp = document.getElementById("temp");

        // Loop through urls
        for (let i = 0; i < imgs.length; i++) {
            // Sleep for 0.5s
            await new Promise((resolve) => setTimeout(resolve, 500));
            let img = new Image();
            img.src = "data:image/png;base64," + imgs[i];
            img.width = 200;
            temp.appendChild(img);
            scrollToBottom();
        }
        temp.removeAttribute("id");
        sendbtn.disabled = false;
        userinputarea.disabled = false;
    }
    */
    scrollToBottom();
};

// Initial message
function insertMessage() {
    let upperdiv = document.getElementById("upperid");
    let sendbtn = document.getElementById("sendbtn");
    let userinputarea = document.getElementById("userinput");
    sendbtn.disabled = true;
    userinputarea.disabled = true;
    let message = "Hello {{ current_user.name }}, this is a message!";
    upperdiv.innerHTML =
        upperdiv.innerHTML +
        `<div class="message">
        <div class="chatbotheader">
            <img src="https://psc2.cf2.poecdn.net/e624182724b2f7d087d86e14094be569c56fc207/_next/static/media/assistant.b077c338.svg" alt="chatbotheader" class="chatbotheaderimage" />
            <div class="chatbotheadername">Tuan Dep Trai</div>
        </div>
        <div class="appmessagediv">
            <div class="appmessage" id="temp">
            </div>
        </div>
    </div>`;
    let temp = document.getElementById("temp");
    let index = 0;
    function displayNextLetter() {
        scrollToBottom();
        if (index < message.length) {
            temp.innerHTML = temp.innerHTML + message[index];
            index++;
            setTimeout(displayNextLetter, 30);
        } else {
            temp.removeAttribute("id");
            sendbtn.disabled = false;
            userinputarea.disabled = false;
        }
    }
    displayNextLetter();
    scrollToBottom();
}
insertMessage();