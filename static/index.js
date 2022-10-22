let uploading = false;
let file = null;

/**
 * Clicks on the hidden file input element
 */
function openFileExplorer() {
    document.getElementById('file-input').click();
}

/**
 * Drop handler of the drop zone
 */
function dropHandler(e) {
    dataTransfer = e.dataTransfer;
    e.preventDefault();
    if (dataTransfer.files.length > 1) {
        //nur 1 file erlaubt aktuell
    } else {
        file = dataTransfer.files[0];
        showUploadButton();
    }
}

/**
 * Handler for the file change event of the file input
 */
function fileChange(e) {
    e.preventDefault();
    var fileList = document.getElementById('file-input').files;
    var f = fileList[0];
    if (f) {
        file = f;
        showUploadButton();
    }
}

function dragOverHandler(e) {
    e.preventDefault();
}

function dragEnterHandler(e) {
    e.preventDefault();
    document.getElementById('drop_zone').classList.add('dragover');
    console.log("drag enter")
}

 function dragLeaveHandler(e) {
    e.preventDefault();
    document.getElementById('drop_zone').classList.remove('dragover');
    console.log("drag leave")
}

/**
 * Upload the file to the server and redirect on success
 */
async function upload() {
    if (extern) {
        let url_response = await fetch('/u')
        if (!url_response.ok) {
            openModal(document.getElementById('error-modal'));
            return
        }
        let url = await url_response.text()

        var formData = new FormData();
        var client = new XMLHttpRequest();
        
        var json = JSON.parse(url)
        url = json['url']
        formData.append('key', json['key'])
        formData.append('x-amz-algorithm', json['x-amz-algorithm'])
        formData.append('x-amz-credential', json['x-amz-credential'])
        formData.append('x-amz-date', json['x-amz-date'])
        formData.append('policy', json['policy'])
        formData.append('x-amz-signature', json['x-amz-signature'])

        file.name = json['key']
        formData.append('file', file);
    
        client.onerror = () => {
            openModal(document.getElementById('error-modal'));
            resetProgress();
        }

        client.onload = e => {
            if (e.target.status == 204) {
                window.location.replace("/f/" + json['key'])
            }
            openModal(document.getElementById('error-modal'));
            resetProgress();
        }

        client.upload.onprogress = e => {
            document.getElementById('progress').value = 100/e.total * e.loaded;
        }

        document.getElementById('progress').classList.remove('hidden');

        client.open("POST", url)
        client.send(formData);
    } else {
        var formData = new FormData();
        var client = new XMLHttpRequest();
        formData.append('file', file);

        client.onerror = e => {
            openModal(document.getElementById('error-modal'));
            resetProgress();
        }

        client.onload = e => {
            if (e.target.status == 200) {
                window.location.replace("/f/" + e.target.response)
            }
            openModal(document.getElementById('error-modal'));
            resetProgress();
        }

        client.upload.onprogress = e => {
            document.getElementById('progress').value = 100/e.total * e.loaded;
        }

        document.getElementById('progress').classList.remove('hidden');

        client.open("POST", "u")
        client.send(formData);
    }
}

/**
 * Reset the progess bar to 0% and hide it
 */
function resetProgress() {
    progress = document.getElementById('progress');
    progress.classList.add('hidden');
    progress.value = 0;
}

/**
 * Switch the view to the upload dialog
 */
function showUploadButton() { 
    document.getElementById('file_name').innerHTML = file.name;
    document.getElementById('drop_container').classList.add('deactivated');
    document.getElementById('upload_dialog').classList.remove('deactivated');
}

/**
 * Switch the view to the initial drag and drop view
 */
function showDropzone() {
    resetProgress();
    document.getElementById('upload_dialog').classList.add('deactivated');
    document.getElementById('drop_container').classList.remove('deactivated');
}