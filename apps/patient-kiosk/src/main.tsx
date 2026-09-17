import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useNavigate,
} from 'react-router-dom'
import axios from 'axios'
import {
  ChevronRight,
  FileUp,
  Globe2,
  HeartPulse,
  LogIn,
  LogOut,
  Mic,
  ShieldCheck,
  UserPlus,
  Volume2,
} from 'lucide-react'
import './styles.css'

const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
})

type Patient = {
  id: string
  patient_code: string
  full_name: string
  dob: string
  sex: string
  phone?: string
  address?: string
  preferred_language?: string
}

type Session = {
  kiosk_token: string
  encounter_id: string
  patient: Patient
  token: string
}

type PatientAuth = {
  access_token: string
  refresh_token: string
  token_type: string
  role: string
  patient: Patient
}

type Question = {
  id: string
  category: string
  question: string
  options: string[]
}

type State = {
  language: 'en' | 'hi'
  session?: Session
  patientAuth?: PatientAuth
}

const savedLanguage = sessionStorage.getItem('language')

const state: State = {
  language:
    savedLanguage === 'hi' || savedLanguage === 'en'
      ? savedLanguage
      : 'en',
}

function loadPatientAuth(): PatientAuth | undefined {
  const raw = sessionStorage.getItem('patientAuth')

  if (!raw) {
    return undefined
  }

  try {
    const parsed = JSON.parse(raw) as PatientAuth

    if (
      parsed.role === 'PATIENT' &&
      parsed.access_token &&
      parsed.patient?.id
    ) {
      return parsed
    }

    sessionStorage.removeItem('patientAuth')
    return undefined
  } catch {
    sessionStorage.removeItem('patientAuth')
    return undefined
  }
}

state.patientAuth = loadPatientAuth()

const dictionary = {
  en: {
    tagline: 'Your information, organized before your consultation.',
    start: 'Start',
    help: 'Need help? Ask a member of staff.',
    back: 'Back',
    next: 'Continue',
  },
  hi: {
    tagline: 'परामर्श से पहले आपकी जानकारी व्यवस्थित।',
    start: 'शुरू करें',
    help: 'मदद चाहिए? स्टाफ के सदस्य से पूछें।',
    back: 'वापस',
    next: 'जारी रखें',
  },
}

function title() {
  return (
    <div className="brand">
      <div className="brand-mark">
        <HeartPulse size={30} />
      </div>
      <span>
        MEDI<span>KIOSK</span>
      </span>
    </div>
  )
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <main className="kiosk">
      <header>
        {title()}
        <div className="secure">
          <ShieldCheck size={18} />
          Private & secure
        </div>
      </header>

      {children}

      <footer>
        <span>{dictionary[state.language].help}</span>
        <span>Clinical decisions are always made by your doctor.</span>
      </footer>
    </main>
  )
}

function PatientAuthPage() {
  const nav = useNavigate()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [loginEmail, setLoginEmail] = useState('')
  const [loginPassword, setLoginPassword] = useState('')

  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [dateOfBirth, setDateOfBirth] = useState('')
  const [gender, setGender] = useState('male')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [address, setAddress] = useState('')
  const [preferredLanguage, setPreferredLanguage] = useState<'en' | 'hi'>('en')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const savePatientAuth = (data: PatientAuth) => {
    state.patientAuth = data
    sessionStorage.setItem('patientAuth', JSON.stringify(data))
  }

  const login = async (event: React.FormEvent) => {
    event.preventDefault()

    setError('')
    setSuccess('')
    setLoading(true)

    try {
      const response = await api.post('/patient-auth/login', {
        email: loginEmail.trim(),
        password: loginPassword,
      })

      savePatientAuth(response.data)

      state.language =
        response.data.patient.preferred_language === 'hi'
          ? 'hi'
          : 'en'

      sessionStorage.setItem('language', state.language)

      nav('/welcome')
    } catch (error: any) {
      setError(
        error.response?.data?.detail ||
          'Unable to sign in. Please check your email and password.',
      )
    } finally {
      setLoading(false)
    }
  }

  const register = async (event: React.FormEvent) => {
    event.preventDefault()

    setError('')
    setSuccess('')

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)

    try {
      const response = await api.post('/patient-auth/register', {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        date_of_birth: dateOfBirth,
        gender,
        phone: phone.trim(),
        email: email.trim(),
        address: address.trim(),
        preferred_language: preferredLanguage,
        password,
        confirm_password: confirmPassword,
      })

      savePatientAuth(response.data)

      state.language = preferredLanguage
      sessionStorage.setItem('language', preferredLanguage)

      setSuccess(
        `Account created successfully. Your patient ID is ${response.data.patient.patient_code}.`,
      )

      nav('/welcome')
    } catch (error: any) {
      setError(
        error.response?.data?.detail ||
          'Unable to create your account. Please check your information and try again.',
      )
    } finally {
      setLoading(false)
    }
  }

  const continueDemo = () => {
    state.patientAuth = undefined
    state.session = undefined
    sessionStorage.removeItem('patientAuth')
    nav('/welcome')
  }

  return (
    <Shell>
      <section className="step patient-auth">
        <div className="eyebrow">PATIENT PORTAL</div>

        <h2>
          {mode === 'login'
            ? 'Sign in to your patient account'
            : 'Create your patient account'}
        </h2>

        <p>
          {mode === 'login'
            ? 'Use the email and password you created for MediKiosk.'
            : 'Create an account to securely use MediKiosk for future consultations.'}
        </p>

        {error && <div className="error">{error}</div>}
        {success && <div className="notice">{success}</div>}

        {mode === 'login' ? (
          <form onSubmit={login}>
            <label className="answer-input">
              <span>Email</span>
              <input
                type="email"
                value={loginEmail}
                onChange={(event) => setLoginEmail(event.target.value)}
                placeholder="you@example.com"
                required
                autoComplete="email"
              />
            </label>

            <label className="answer-input">
              <span>Password</span>
              <input
                type="password"
                value={loginPassword}
                onChange={(event) => setLoginPassword(event.target.value)}
                placeholder="Enter your password"
                required
                minLength={8}
                autoComplete="current-password"
              />
            </label>

            <button className="primary wide" disabled={loading}>
              <LogIn size={18} />
              {loading ? 'Signing in…' : 'Sign in'}
              {!loading && <ChevronRight />}
            </button>
          </form>
        ) : (
          <form onSubmit={register}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
                gap: '14px',
              }}
            >
              <label className="answer-input">
                <span>First name</span>
                <input
                  type="text"
                  value={firstName}
                  onChange={(event) => setFirstName(event.target.value)}
                  placeholder="First name"
                  required
                  autoComplete="given-name"
                />
              </label>

              <label className="answer-input">
                <span>Last name</span>
                <input
                  type="text"
                  value={lastName}
                  onChange={(event) => setLastName(event.target.value)}
                  placeholder="Last name"
                  required
                  autoComplete="family-name"
                />
              </label>

              <label className="answer-input">
                <span>Date of birth</span>
                <input
                  type="date"
                  value={dateOfBirth}
                  onChange={(event) =>
                    setDateOfBirth(event.target.value)
                  }
                  required
                />
              </label>

              <label className="answer-input">
                <span>Gender</span>
                <select
                  value={gender}
                  onChange={(event) => setGender(event.target.value)}
                  required
                >
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                  <option value="prefer_not_to_say">
                    Prefer not to say
                  </option>
                </select>
              </label>
            </div>

            <label className="answer-input">
              <span>Phone</span>
              <input
                type="tel"
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                placeholder="10-digit mobile number"
                required
                autoComplete="tel"
              />
            </label>

            <label className="answer-input">
              <span>Email</span>
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                required
                autoComplete="email"
              />
            </label>

            <label className="answer-input">
              <span>Address</span>
              <textarea
                value={address}
                onChange={(event) => setAddress(event.target.value)}
                placeholder="Enter your address"
                required
                rows={3}
              />
            </label>

            <label className="answer-input">
              <span>Preferred language</span>
              <select
                value={preferredLanguage}
                onChange={(event) =>
                  setPreferredLanguage(
                    event.target.value === 'hi' ? 'hi' : 'en',
                  )
                }
              >
                <option value="en">English</option>
                <option value="hi">हिन्दी</option>
              </select>
            </label>

            <label className="answer-input">
              <span>Password</span>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Minimum 8 characters"
                required
                minLength={8}
                autoComplete="new-password"
              />
            </label>

            <label className="answer-input">
              <span>Confirm password</span>
              <input
                type="password"
                value={confirmPassword}
                onChange={(event) =>
                  setConfirmPassword(event.target.value)
                }
                placeholder="Re-enter your password"
                required
                minLength={8}
                autoComplete="new-password"
              />
            </label>

            <button className="primary wide" disabled={loading}>
              <UserPlus size={18} />
              {loading
                ? 'Creating account…'
                : 'Create patient account'}
              {!loading && <ChevronRight />}
            </button>
          </form>
        )}

        <div
          className="action-row"
          style={{
            marginTop: '20px',
            alignItems: 'center',
          }}
        >
          <button
            type="button"
            className="secondary"
            onClick={() => {
              setError('')
              setSuccess('')
              setMode(mode === 'login' ? 'register' : 'login')
            }}
          >
            {mode === 'login'
              ? 'Create new account'
              : 'Already have an account? Sign in'}
          </button>

          <button
            type="button"
            className="text-button"
            onClick={continueDemo}
          >
            Continue with demo patient
          </button>
        </div>
      </section>
    </Shell>
  )
}

function Welcome() {
  const nav = useNavigate()
  const d = dictionary[state.language]

  return (
    <Shell>
      <section className="hero">
        <div className="eyebrow">PRE-CONSULTATION INTAKE</div>

        <h1>
          From your voice to a<br />
          <em>doctor-ready timeline.</em>
        </h1>

        <p>{d.tagline}</p>

        <button
          className="primary start"
          onClick={() => nav('/language')}
        >
          {d.start}
          <ChevronRight />
        </button>

        {state.patientAuth && (
          <div className="privacy">
            <ShieldCheck />
            Signed in as {state.patientAuth.patient.full_name}
          </div>
        )}

        <div className="privacy">
          <ShieldCheck />
          Your answers and documents are shared only with your care team
          for review.
        </div>

        {state.patientAuth && (
          <button
            className="text-button"
            onClick={() => {
              state.patientAuth = undefined
              state.session = undefined
              sessionStorage.removeItem('patientAuth')
              nav('/patient-login')
            }}
          >
            <LogOut size={16} />
            Sign out
          </button>
        )}
      </section>
    </Shell>
  )
}

function Language() {
  const nav = useNavigate()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const selectLanguage = async (language: 'en' | 'hi') => {
    state.language = language
    sessionStorage.setItem('language', language)

    if (!state.patientAuth) {
      nav('/identify')
      return
    }

    setError('')
    setLoading(true)

    try {
      const response = await api.post('/kiosk/identify', {
        patient_id: state.patientAuth.patient.id,
        language,
      })

      state.session = response.data
      nav('/consent')
    } catch {
      setError(
        'Unable to start your secure session. Please retry.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <Shell>
      <section className="step">
        <div className="eyebrow">STEP 1 OF 4</div>

        <h2>Select your language</h2>

        <p>
          Choose the language you are most comfortable using.
        </p>

        {error && <div className="error">{error}</div>}

        <div className="language-grid">
          <button
            className="language"
            disabled={loading}
            onClick={() => selectLanguage('en')}
          >
            <Globe2 />
            <strong>English</strong>
            <small>Continue in English</small>
          </button>

          <button
            className="language"
            disabled={loading}
            onClick={() => selectLanguage('hi')}
          >
            <Globe2 />
            <strong>हिन्दी</strong>
            <small>हिंदी में जारी रखें</small>
          </button>
        </div>

        <button
          className="text-button"
          onClick={() => nav('/welcome')}
        >
          ← Back
        </button>
      </section>
    </Shell>
  )
}

function Identify() {
  const nav = useNavigate()
  const [patients, setPatients] = useState<Patient[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get('/kiosk/demo-patients')
      .then((response) => setPatients(response.data))
      .catch(() =>
        setError(
          'Unable to load demo patients. Please retry.',
        ),
      )
  }, [])

  const select = async (patient: Patient) => {
    try {
      const response = await api.post('/kiosk/identify', {
        patient_id: patient.id,
        language: state.language,
      })

      state.session = response.data
      nav('/consent')
    } catch {
      setError(
        'Unable to start a secure session. Please retry.',
      )
    }
  }

  return (
    <Shell>
      <section className="step">
        <div className="eyebrow">STEP 2 OF 4</div>

        <h2>Identify yourself</h2>

        <p>
          For this safe demo, select a synthetic patient profile.
          No real patient data is shown.
        </p>

        {error && <div className="error">{error}</div>}

        <div className="patient-list">
          {patients.map((patient) => (
            <button
              className="patient"
              key={patient.id}
              onClick={() => select(patient)}
            >
              <span className="avatar">
                {patient.full_name
                  .split(' ')
                  .map((x) => x[0])
                  .join('')}
              </span>

              <span>
                <strong>{patient.full_name}</strong>
                <small>
                  {patient.patient_code} · {patient.sex}
                </small>
              </span>

              <ChevronRight />
            </button>
          ))}
        </div>

        <button
          className="text-button"
          onClick={() => nav('/language')}
        >
          ← Back
        </button>
      </section>
    </Shell>
  )
}

function ConsentPage() {
  const nav = useNavigate()
  const [error, setError] = useState('')

  const answer = async (agreed: boolean) => {
    if (!state.session) {
      return nav('/welcome')
    }

    try {
      await api.post(
        '/kiosk/consent',
        { agreed },
        {
          headers: {
            'X-Kiosk-Session': state.session.kiosk_token,
          },
        },
      )

      agreed ? nav('/interview') : nav('/welcome')
    } catch {
      setError(
        'We could not record your choice. Please retry.',
      )
    }
  }

  return (
    <Shell>
      <section className="step consent">
        <div className="eyebrow">STEP 3 OF 4</div>

        <h2>Your consent matters</h2>

        <p>
          Before we begin, please understand how this kiosk
          supports your consultation.
        </p>

        <div className="consent-card">
          <ShieldCheck />

          <div>
            <strong>What we collect</strong>
            <span>
              Your symptoms, health history and any document you
              choose to upload.
            </span>
          </div>

          <div>
            <strong>Why we collect it</strong>
            <span>
              To organize a pre-consultation record for your doctor
              and care team.
            </span>
          </div>

          <div>
            <strong>Your clinician remains in charge</strong>
            <span>
              This system does not diagnose, prescribe, or make
              clinical decisions.
            </span>
          </div>
        </div>

        {error && <div className="error">{error}</div>}

        <div className="action-row">
          <button
            className="secondary"
            onClick={() => answer(false)}
          >
            Decline
          </button>

          <button
            className="primary"
            onClick={() => answer(true)}
          >
            Agree & continue
            <ChevronRight />
          </button>
        </div>
      </section>
    </Shell>
  )
}

function Interview() {
  const nav = useNavigate()

  const [question, setQuestion] = useState<Question>()
  const [answer, setAnswer] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState('')

  const headers = () => ({
    'X-Kiosk-Session': state.session?.kiosk_token || '',
  })

  const load = () =>
    api
      .get('/kiosk/interview/current', {
        headers: headers(),
      })
      .then((response) => {
        if (response.data.complete) {
          nav('/complete')
          return
        }

        setQuestion(response.data.question)
        setAnswer('')
        setLoading(false)
      })
      .catch(() => {
        setNotice(
          'We could not load the next question. Please retry.',
        )
        setLoading(false)
      })

  useEffect(() => {
    if (!state.session) {
      nav('/welcome')
    } else {
      load()
    }
  }, [])

  const submit = async (value = answer) => {
    if (!question || !value.trim()) {
      return setNotice(
        'Please choose an option or type your answer.',
      )
    }

    try {
      setNotice('')
      setLoading(true)

      const response = await api.post(
        '/kiosk/interview/answer',
        {
          question_id: question.id,
          answer: value,
          input_method: 'text',
        },
        {
          headers: headers(),
        },
      )

      if (response.data.potential_red_flags) {
        setNotice(
          'Potential urgent symptoms have been shared with the care team for early attention.',
        )
      }

      if (response.data.next) {
        setQuestion(response.data.next)
        setAnswer('')
        setLoading(false)
      } else {
        nav('/documents')
      }
    } catch (error: any) {
      setNotice(
        error.response?.data?.detail ||
          'Unable to save your answer. Please retry.',
      )
      setLoading(false)
    }
  }

  const voice = () => {
    const Recognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition

    if (!Recognition) {
      setNotice(
        'Voice input is not available here. Please use touch or text input.',
      )
      return
    }

    const recognition = new Recognition()

    recognition.lang =
      state.language === 'hi' ? 'hi-IN' : 'en-IN'

    recognition.onresult = (event: any) =>
      setAnswer(event.results[0][0].transcript)

    recognition.start()
  }

  const upload = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0]

    if (!file) {
      return
    }

    try {
      setProcessing(
        'Uploading and processing your document…',
      )

      const form = new FormData()
      form.append('file', file)
      form.append('category', 'Prescription')

      await api.post('/kiosk/documents', form, {
        headers: headers(),
      })

      setProcessing(
        'Document uploaded. OCR is processing in the background.',
      )
    } catch {
      setProcessing(
        'Unable to upload the document. Please try another PDF or image under 10 MB.',
      )
    }
  }

  if (loading && !question) {
    return (
      <Shell>
        <section className="step">
          <div className="loader" />
          Loading your secure interview…
        </section>
      </Shell>
    )
  }

  if (!question) {
    return null
  }

  return (
    <Shell>
      <section className="interview">
        <div className="progress">
          <span>STEP 4 OF 4 · CLINICAL INTAKE</span>

          <div>
            <i style={{ width: '62%' }} />
          </div>
        </div>

        <h2>{question.question}</h2>

        <p className="spoken">
          {answer && <>You said: “{answer}”</>}
        </p>

        <div className="options">
          {question.options.map((option) => (
            <button
              key={option}
              className={
                answer === option ? 'selected' : ''
              }
              onClick={() => setAnswer(option)}
            >
              {option}
            </button>
          ))}
        </div>

        <label className="answer-input">
          <span>Or type your answer</span>

          <textarea
            value={answer}
            onChange={(event) =>
              setAnswer(event.target.value)
            }
            placeholder="Type here…"
          />
        </label>

        <div className="voice-row">
          <button className="voice" onClick={voice}>
            <Mic />
            Speak
          </button>

          <button
            className="icon-button"
            aria-label="Repeat question"
            onClick={() => {
              const utterance =
                new SpeechSynthesisUtterance(
                  question.question,
                )

              utterance.lang =
                state.language === 'hi'
                  ? 'hi-IN'
                  : 'en-IN'

              speechSynthesis.speak(utterance)
            }}
          >
            <Volume2 />
          </button>
        </div>

        {notice && (
          <div className="notice">{notice}</div>
        )}

        <button
          className="primary wide"
          disabled={loading}
          onClick={() => submit()}
        >
          {loading ? 'Saving…' : 'Confirm answer'}
          <ChevronRight />
        </button>

        <div className="upload">
          <label>
            <FileUp />
            Add a previous prescription or report

            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={upload}
            />
          </label>

          {processing && <small>{processing}</small>}
        </div>
      </section>
    </Shell>
  )
}

function Documents() {
  const nav = useNavigate()

  return (
    <Shell>
      <section className="step">
        <div className="eyebrow">INTAKE COMPLETE</div>

        <h2>Anything else to share?</h2>

        <p>
          Your answers are ready for your doctor. You can now
          securely submit your intake.
        </p>

        <button
          className="primary"
          onClick={async () => {
            try {
              await api.post(
                '/kiosk/complete',
                {},
                {
                  headers: {
                    'X-Kiosk-Session':
                      state.session?.kiosk_token,
                  },
                },
              )

              nav('/complete')
            } catch {
              alert('Unable to submit your intake. Please retry.')
            }
          }}
        >
          Submit for review
          <ChevronRight />
        </button>
      </section>
    </Shell>
  )
}

function Complete() {
  const nav = useNavigate()

  return (
    <Shell>
      <section className="step complete">
        <div className="success">
          <ShieldCheck size={46} />
        </div>

        <h2>Thank you. You’re all set.</h2>

        <p>
          Your information has been securely submitted for review.
          A clinician will assess it before or during your
          consultation.
        </p>

        <div className="privacy">
          This system organizes information; it does not provide a
          diagnosis or treatment.
        </div>

        <button
          className="primary"
          onClick={() => {
            state.session = undefined
            nav('/welcome')
          }}
        >
          Finish
        </button>
      </section>
    </Shell>
  )
}

function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={<Navigate to="/patient-login" replace />}
      />

      <Route
        path="/patient-login"
        element={<PatientAuthPage />}
      />

      <Route
        path="/welcome"
        element={<Welcome />}
      />

      <Route
        path="/language"
        element={<Language />}
      />

      <Route
        path="/identify"
        element={<Identify />}
      />

      <Route
        path="/consent"
        element={<ConsentPage />}
      />

      <Route
        path="/interview"
        element={<Interview />}
      />

      <Route
        path="/documents"
        element={<Documents />}
      />

      <Route
        path="/complete"
        element={<Complete />}
      />

      <Route
        path="*"
        element={
          <Navigate
            to="/patient-login"
            replace
          />
        }
      />
    </Routes>
  )
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)