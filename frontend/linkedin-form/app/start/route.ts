import { NextResponse } from "next/server"

// Type definition for the expected request body
type VerificationRequest = {
  email: string
  linkedin: string
  phone: string
}

export async function POST(request: Request) {
  try {
    // Parse the request body
    const body = (await request.json()) as VerificationRequest
    const { email, linkedin, phone } = body

    // Validate required fields
    if (!email || !linkedin || !phone) {
      return NextResponse.json(
        {
          success: false,
          error: "Missing required fields",
        },
        { status: 400 },
      )
    }

    // Log the submission
    console.log("Verification request received:", { email, linkedin, phone })

    // Return success response
    return NextResponse.json(
      {
        success: true,
        message: "Verification request received",
        data: {
          email,
          linkedin,
          phone,
        },
      },
      { status: 200 },
    )
  } catch (error) {
    console.error("Error processing verification request:", error)

    return NextResponse.json(
      {
        success: false,
        error: "Failed to process verification request",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    )
  }
}
