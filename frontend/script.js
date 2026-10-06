const API_URL =
    "https://o7ng5jf54m.execute-api.ap-south-1.amazonaws.com/prod/documents";
const UPLOAD_API_URL =
    "https://o7ng5jf54m.execute-api.ap-south-1.amazonaws.com/prod/upload";

async function loadDocuments() {

    const container =
        document.getElementById("documentsContainer");

    container.innerHTML = "<p>Loading...</p>";

    try {

        const response = await fetch(API_URL);

        if (!response.ok) {
            throw new Error("Failed to fetch documents");
        }

        const documents = await response.json();

        if (documents.length === 0) {

            container.innerHTML =
                "<p>No documents uploaded yet.</p>";

            return;
        }

        container.innerHTML = "";

        documents.forEach(doc => {

            const div =
                document.createElement("div");

            div.className = "document";

            div.innerHTML = `
                <h3>${doc.fileName}</h3>

                <p>
                    Size:
                    ${doc.fileSize} bytes
                </p>

                <p>
                    Status:
                    <span class="status">
                        ${doc.status}
                    </span>
                </p>

                <p>
                    Uploaded:
                    ${doc.uploadTime}
                </p>
            `;

            container.appendChild(div);

        });

    } catch (error) {

        console.error(error);

        container.innerHTML =
            "<p>Unable to load documents.</p>";
    }
}


// Upload function will be implemented later
async function uploadFile() {

    const file =
        document.getElementById("fileInput").files[0];

    const status =
        document.getElementById("uploadStatus");

    if (!file) {

        status.textContent =
            "Please select a file.";

        return;
    }

    try {

        status.textContent =
            "Validating file...";

        // --------------------------------
        // Check file size
        // --------------------------------

        if (file.size > 10 * 1024 * 1024) {

            status.textContent =
                "File must be smaller than 10 MB.";

            return;
        }

        // --------------------------------
        // Allowed file types
        // --------------------------------

        const allowedTypes = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain"
        ];

        if (!allowedTypes.includes(file.type)) {

            status.textContent =
                "Only PDF, DOC, DOCX and TXT files are allowed.";

            return;
        }

        // --------------------------------
        // Request pre-signed URL
        // --------------------------------

        status.textContent =
            "Preparing secure upload...";

        const response = await fetch(
            UPLOAD_API_URL,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    fileName: file.name,
                    fileSize: file.size,
                    contentType: file.type
                })
            }
        );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.message ||
                "Could not prepare upload"
            );
        }

        // --------------------------------
        // Upload directly to S3
        // --------------------------------

        status.textContent =
            "Uploading to Amazon S3...";

        const uploadResponse =
            await fetch(
                data.uploadUrl,
                {
                    method: "PUT",

                    headers: {
                        "Content-Type": file.type
                    },

                    body: file
                }
            );

        if (!uploadResponse.ok) {

            throw new Error(
                "S3 upload failed"
            );
        }

        status.textContent =
            "File uploaded. Processing...";

        // --------------------------------
        // Wait for S3 → Lambda
        // --------------------------------

        setTimeout(() => {

            loadDocuments();

            status.textContent =
                "Document processed successfully.";

        }, 3000);

    }

    catch (error) {

        console.error(error);

        status.textContent =
            "Upload failed: " +
            error.message;
    }
}

loadDocuments();