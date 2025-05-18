"use client"

import type React from "react"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useToast } from "@/hooks/use-toast"
import { Loader2, Briefcase, CheckCircle, Clock, Shield, Phone } from "lucide-react"

export default function Home() {
  const [email, setEmail] = useState("")
  const [linkedin, setLinkedin] = useState("")
  const [phone, setPhone] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const { toast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // Basic validation
    if (!email || !linkedin) {
      toast({
        title: "Missing information",
        description: "Please fill in all fields",
        variant: "destructive",
      })
      return
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      toast({
        title: "Invalid email",
        description: "Please enter a valid email address",
        variant: "destructive",
      })
      return
    }

    // Validate LinkedIn URL format
    if (!linkedin.includes("linkedin.com")) {
      toast({
        title: "Invalid LinkedIn URL",
        description: "Please enter a valid LinkedIn profile URL",
        variant: "destructive",
      })
      return
    }

    // Validate phone number format (basic validation)
    if (!phone || phone.length < 10) {
      toast({
        title: "Invalid phone number",
        description: "Please enter a valid phone number",
        variant: "destructive",
      })
      return
    }

    setIsLoading(true)

    try {
      const response = await fetch("http://0.0.0.0:3000/start", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, linkedin, phone }),
      })

      const result = await response.json()

      if (response.ok && result.success) {
        // Format the scheduled time for display
        const scheduledDate = new Date(result.scheduledTime)
        const formattedDate = scheduledDate.toLocaleDateString("en-US", {
          weekday: "long",
          month: "long",
          day: "numeric",
          hour: "numeric",
          minute: "numeric",
        })

        toast({
          title: "Verification Scheduled!",
          description: `Our AI agent will call you on ${formattedDate} to verify your credentials.`,
        })

        // Reset form
        setEmail("")
        setLinkedin("")
        setPhone("")
      } else {
        toast({
          title: "Something went wrong",
          description: result.error || "There was an error scheduling your verification call",
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Connection error",
        description: "Could not connect to the server",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="w-full max-w-4xl px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-3">AI-Powered Resume Verification</h1>
          <p className="text-slate-300 max-w-2xl mx-auto">
            Ensuring fairness and efficiency in the hiring process through automated credential verification
          </p>
        </div>

        <div className="grid md:grid-cols-5 gap-6">
          <div className="md:col-span-2 flex flex-col justify-center space-y-6 text-white">
            <div className="flex items-start space-x-3">
              <Clock className="h-8 w-8 text-purple-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-lg text-purple-300">Save Time</h3>
                <p className="text-slate-300 text-sm">Streamline the recruitment process with automated verification</p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <Shield className="h-8 w-8 text-purple-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-lg text-purple-300">Ensure Fairness</h3>
                <p className="text-slate-300 text-sm">Standardized verification process for all candidates</p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <Phone className="h-8 w-8 text-purple-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-lg text-purple-300">AI Phone Verification</h3>
                <p className="text-slate-300 text-sm">Our AI agent will call to verify your resume credentials</p>
              </div>
            </div>
          </div>

          <Card className="md:col-span-3 shadow-2xl border-0 bg-white/10 backdrop-blur-md">
            <CardHeader className="space-y-1 border-b border-white/10 pb-6">
              <div className="flex justify-center mb-2">
                <div className="p-3 rounded-full bg-purple-600/20 border border-purple-500/30">
                  <Briefcase className="h-6 w-6 text-purple-400" />
                </div>
              </div>
              <CardTitle className="text-2xl font-bold text-center text-white">Get Verified</CardTitle>
              <CardDescription className="text-center text-slate-300">
                Enter your details to schedule an AI verification call
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleSubmit}>
              <CardContent className="space-y-4 pt-6">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-white">
                    Email address
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="bg-white/10 border-white/20 text-white placeholder:text-slate-400 focus:border-purple-500 focus:ring-purple-500"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="linkedin" className="text-white">
                    LinkedIn profile
                  </Label>
                  <Input
                    id="linkedin"
                    type="url"
                    placeholder="https://linkedin.com/in/yourprofile"
                    value={linkedin}
                    onChange={(e) => setLinkedin(e.target.value)}
                    required
                    className="bg-white/10 border-white/20 text-white placeholder:text-slate-400 focus:border-purple-500 focus:ring-purple-500"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone" className="text-white">
                    Phone number
                  </Label>
                  <Input
                    id="phone"
                    type="tel"
                    placeholder="(123) 456-7890"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    required
                    className="bg-white/10 border-white/20 text-white placeholder:text-slate-400 focus:border-purple-500 focus:ring-purple-500"
                  />
                </div>
              </CardContent>
              <CardFooter>
                <Button
                  type="submit"
                  className="w-full bg-gradient-to-r from-purple-600 to-violet-600 hover:from-purple-700 hover:to-violet-700 transition-all duration-300 text-white border-0 shadow-lg shadow-purple-900/30"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Scheduling verification...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="mr-2 h-4 w-4" />
                      Schedule Verification Call
                    </>
                  )}
                </Button>
              </CardFooter>
            </form>
          </Card>
        </div>

        <div className="mt-8 text-center text-sm text-slate-400">
          <p>By submitting, you agree to our verification process and privacy policy.</p>
        </div>
      </div>
    </main>
  )
}
