import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import axios from 'axios'
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  FileText,
  LogOut,
  Search,
  ShieldCheck,
  Stethoscope,
  Users
} from 'lucide-react'
import './styles.css'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
})

type Session = {
  token: string
  role: string
  name: string
}

type Encounter = {
  id: string
  token: string
  status: string
  priority: string
  patient: {
    full_name: string
    patient_code: string
    sex: string
    dob: string
  }
}

type Detail = Encounter & {
  department: string
  answers: any[]
  documents: any[]
  entities: any[]
  timeline: any[]
  red_flags: any[]
  summary: any
}

let session: Session | undefined = (() => {
  const stored = localStorage.getItem('medikiosk-doctor')
  return stored ? JSON.parse(stored) : undefined
})()

const headers = () => ({
  Authorization: `Bearer ${session?.token || ''}`
})

function Badge({ value }: { value: string }) {
  return (
    <span className={`badge ${value.toLowerCase().replaceAll('_', '-')}`}>
      {value.replaceAll('_', ' ')}
    </span>
  )
}

function Login({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState('doctor@medikiosk.local')
  const [password, setPassword] = useState('DemoPass123!')
  const [error, setError] = useState('')

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      const response = await api.post('/auth/login', {
        email,
        password
      })

      if (!['DOCTOR', 'ADMIN'].includes(response.data.role)) {
        throw new Error(
          'This account does not have clinical-review access.'
        )
      }

      session = {
        token: response.data.access_token,
        role: response.data.role,
        name: response.data.user.full_name
      }

      localStorage.setItem(
        'medikiosk-doctor',
        JSON.stringify(session)
      )

      onLogin()
    } catch (error: any) {
      setError(
        error.response?.data?.detail ||
          error.message ||
          'Unable to sign in.'
      )
    }
  }

  return (
    <div className="login">
      <section>
        <div className="logo">
          <Stethoscope /> MEDI<span>KIOSK</span>
        </div>

        <div className="login-copy">
          <div className="eyebrow">
            CLINICAL REVIEW WORKSPACE
          </div>

          <h1>
            See the story
            <br />
            behind the symptoms.
          </h1>

          <p>
            Evidence-linked pre-consultation records for clinician
            review. MediKiosk does not make diagnoses or treatment
            decisions.
          </p>
        </div>

        <form onSubmit={submit}>
          <label>
            Email
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              type="email"
            />
          </label>

          <label>
            Password
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type="password"
            />
          </label>

          {error && <div className="error">{error}</div>}

          <button>
            Sign in to clinical review
            <ChevronRight />
          </button>

          <small>
            Demo access uses only synthetic patient data.
          </small>
        </form>
      </section>
    </div>
  )
}

function Side({
  page,
  setPage
}: {
  page: string
  setPage: (page: string) => void
}) {
  const items = [
    ['dashboard', Activity, 'Dashboard'],
    ['patients', Users, 'Patients'],
    ['alerts', AlertTriangle, 'Triage alerts']
  ] as const

  return (
    <aside>
      <div className="logo">
        <Stethoscope /> MEDI<span>KIOSK</span>
      </div>

      <div className="role">CLINICAL REVIEW</div>

      <nav>
        {items.map(([id, Icon, label]) => (
          <button
            key={id}
            className={page === id ? 'active' : ''}
            onClick={() => setPage(id)}
          >
            <Icon size={19} />
            {label}
          </button>
        ))}
      </nav>

      <div className="side-bottom">
        <span>
          <ShieldCheck />
          Signed in as {session?.name}
        </span>

        <button
          onClick={() => {
            localStorage.removeItem('medikiosk-doctor')
            location.reload()
          }}
        >
          <LogOut size={17} />
          Sign out
        </button>
      </div>
    </aside>
  )
}

function Dashboard({
  select
}: {
  select: (id: string) => void
}) {
  const [data, setData] = useState<any>()

  useEffect(() => {
    api
      .get('/dashboard/doctor', {
        headers: headers()
      })
      .then((response) => setData(response.data))
  }, [])

  if (!data) {
    return <Loading />
  }

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <div className="eyebrow">
            TODAY'S CLINICAL OVERVIEW
          </div>

          <h2>
            Good morning, {session?.name.split(' ')[0]}.
          </h2>

          <p>
            Review patient-reported history alongside traceable
            evidence.
          </p>
        </div>

        <button
          className="outline"
          onClick={() => location.reload()}
        >
          Refresh data
        </button>
      </div>

      <div className="metrics">
        <Metric
          label="Today's patients"
          value={data.today_patients}
          icon={<Users />}
        />

        <Metric
          label="Pending review"
          value={data.pending_reviews}
          icon={<ClipboardList />}
        />

        <Metric
          label="Early-attention alerts"
          value={data.high_priority_cases}
          danger
          icon={<AlertTriangle />}
        />

        <Metric
          label="Completed intake"
          value={data.completed_consultations}
          icon={<CheckCircle2 />}
        />
      </div>

      <section className="panel">
        <div className="panel-head">
          <h3>Recent encounters</h3>
          <span>Live data from MediKiosk API</span>
        </div>

        <div className="table">
          {data.recent_encounters.map((encounter: any) => (
            <button
              onClick={() => select(encounter.id)}
              key={encounter.id}
            >
              <span>
                <strong>{encounter.patient}</strong>
                <small>{encounter.token}</small>
              </span>

              <span>
                <Badge value={encounter.priority} />
              </span>

              <span>
                <Badge value={encounter.status} />
              </span>

              <ChevronRight />
            </button>
          ))}
        </div>
      </section>
    </section>
  )
}

function Metric({
  label,
  value,
  icon,
  danger
}: {
  label: string
  value: string | number
  icon: any
  danger?: boolean
}) {
  return (
    <div className={`metric ${danger ? 'danger' : ''}`}>
      <div>{icon}</div>
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  )
}

function Loading() {
  return (
    <section className="page loading">
      <div className="spinner" />
      Loading clinical data…
    </section>
  )
}

function Encounters({
  select
}: {
  select: (id: string) => void
}) {
  const [items, setItems] = useState<Encounter[]>([])
  const [filter, setFilter] = useState('')

  useEffect(() => {
    api
      .get('/encounters', {
        headers: headers()
      })
      .then((response) => setItems(response.data))
  }, [])

  const filtered = items.filter((encounter) =>
    (
      encounter.patient.full_name +
      encounter.token
    )
      .toLowerCase()
      .includes(filter.toLowerCase())
  )

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <div className="eyebrow">PATIENT RECORDS</div>
          <h2>Encounters</h2>
          <p>
            Only authorized clinical users can open these records.
          </p>
        </div>
      </div>

      <label className="search">
        <Search />
        <input
          placeholder="Search patient or token"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
      </label>

      <section className="panel table">
        <div className="th">
          <span>Patient</span>
          <span>Priority</span>
          <span>Status</span>
          <span />
        </div>

        {filtered.map((encounter) => (
          <button
            onClick={() => select(encounter.id)}
            key={encounter.id}
          >
            <span>
              <strong>{encounter.patient.full_name}</strong>
              <small>
                {encounter.patient.patient_code} · Token{' '}
                {encounter.token}
              </small>
            </span>

            <span>
              <Badge value={encounter.priority} />
            </span>

            <span>
              <Badge value={encounter.status} />
            </span>

            <ChevronRight />
          </button>
        ))}
      </section>
    </section>
  )
}

function Alerts({
  select
}: {
  select: (id: string) => void
}) {
  const [items, setItems] = useState<any[]>([])

  useEffect(() => {
    api
      .get('/red-flags', {
        headers: headers()
      })
      .then((response) => setItems(response.data))
  }, [])

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <div className="eyebrow">TRIAGE VISIBILITY</div>
          <h2>Potential early-attention alerts</h2>
          <p>
            Alerts are deterministic safety prompts, not clinical
            diagnoses.
          </p>
        </div>
      </div>

      <div className="alert-list">
        {items.map((item) => (
          <button
            onClick={() => select(item.encounter_id)}
            key={item.id}
            className="alert"
          >
            <AlertTriangle />

            <span>
              <Badge value={item.priority} />

              <strong>
                {item.patient} · {item.token}
              </strong>

              <p>{item.reason}</p>

              <small>{item.recommended_action}</small>
            </span>

            <ChevronRight />
          </button>
        ))}
      </div>
    </section>
  )
}

function DetailView({
  id,
  back
}: {
  id: string
  back: () => void
}) {
  const [data, setData] = useState<Detail>()
  const [edit, setEdit] = useState(false)
  const [text, setText] = useState('')
  const [message, setMessage] = useState('')

  const load = () =>
    api
      .get(`/encounters/${id}`, {
        headers: headers()
      })
      .then((response) => {
        setData(response.data)
        setText(response.data.summary?.content || '')
      })

  useEffect(() => {
    load()
  }, [id])

  const verify = async () => {
    await api.post(
      `/encounters/${id}/summary/verify`,
      {},
      {
        headers: headers()
      }
    )

    setMessage(
      'Summary verified by clinician. FHIR-compatible record is now ready.'
    )

    load()
  }

  const save = async () => {
    await api.put(
      `/encounters/${id}/summary`,
      {
        content: text
      },
      {
        headers: headers()
      }
    )

    setEdit(false)
    setMessage('Draft saved.')
    load()
  }

  const source = async (document: any) => {
    const response = await api.get(document.source_url, {
      headers: headers(),
      responseType: 'blob'
    })

    window.open(
      URL.createObjectURL(response.data),
      '_blank',
      'noopener'
    )
  }

  const openFhir = async () => {
    const response = await api.get(
      `/encounters/${id}/fhir`,
      {
        headers: headers()
      }
    )

    const url = URL.createObjectURL(
      new Blob(
        [JSON.stringify(response.data, null, 2)],
        {
          type: 'application/json'
        }
      )
    )

    window.open(url, '_blank', 'noopener')
  }

  const sync = async (
    target: 'his' | 'abdm'
  ) => {
    try {
      const response = await api.post(
        `/encounters/${id}/integrations/${target}`,
        {},
        {
          headers: headers()
        }
      )

      setMessage(response.data.message)
    } catch (error: any) {
      setMessage(
        error.response?.data?.detail ||
          `Unable to sync with ${target.toUpperCase()}.`
      )
    }
  }

  if (!data) {
    return <Loading />
  }

  return (
    <section className="page detail">
      <button className="back" onClick={back}>
        ← All encounters
      </button>

      <div className="patient-header">
        <div>
          <div className="eyebrow">
            ENCOUNTER · {data.token}
          </div>

          <h2>{data.patient.full_name}</h2>

          <p>
            {data.patient.patient_code} · {data.patient.sex} ·
            DOB {data.patient.dob} · {data.department}
          </p>
        </div>

        <Badge value={data.priority} />
      </div>

      {message && (
        <div className="success-msg">
          {message}
        </div>
      )}

      <div className="detail-grid">
        <div className="left-col">
          <Panel
            title="Current complaint"
            icon={<Activity />}
          >
            <div className="answer-list">
              {data.answers.map((answer) => (
                <div key={answer.id}>
                  <strong>
                    {answer.question_id.replaceAll(
                      '_',
                      ' '
                    )}
                  </strong>

                  <span>
                    {answer.raw_answer}
                    <small>Patient reported</small>
                  </span>
                </div>
              ))}
            </div>
          </Panel>

          <Panel
            title="Evidence-linked clinical timeline"
            icon={<ClipboardList />}
          >
            <div className="timeline">
              {data.timeline.map((timeline) => (
                <div key={timeline.id}>
                  <i />

                  <span>
                    <small>
                      {timeline.date || 'Current visit'} ·{' '}
                      {timeline.source.replaceAll(
                        '_',
                        ' '
                      )}
                    </small>

                    <strong>{timeline.title}</strong>

                    <p>{timeline.description}</p>
                  </span>
                </div>
              ))}
            </div>
          </Panel>

          <Panel
            title="Previous medical documents"
            icon={<FileText />}
          >
            <div className="documents">
              {data.documents.length ? (
                data.documents.map((document) => (
                  <div key={document.id}>
                    <span>
                      <FileText />

                      <strong>
                        {document.filename}

                        <small>
                          {document.category} · OCR{' '}
                          {Math.round(
                            document.confidence * 100
                          )}
                          % · {document.status}
                        </small>
                      </strong>
                    </span>

                    <button
                      className="outline"
                      onClick={() =>
                        source(document)
                      }
                    >
                      View source
                    </button>
                  </div>
                ))
              ) : (
                <p className="empty">
                  No documents for this encounter.
                </p>
              )}
            </div>
          </Panel>
        </div>

        <div className="right-col">
          <Panel
            title="Potential red flags"
            icon={<AlertTriangle />}
          >
            {data.red_flags.length ? (
              data.red_flags.map((flag) => (
                <div className="flag" key={flag.id}>
                  <Badge value={flag.priority} />
                  <p>{flag.reason}</p>
                  <small>
                    {flag.recommended_action}
                  </small>
                </div>
              ))
            ) : (
              <p className="empty">
                No configured potential red flags detected.
              </p>
            )}
          </Panel>

          <Panel
            title="Doctor-ready summary"
            icon={<Stethoscope />}
          >
            <div className="summary">
              <Badge
                value={
                  data.summary?.verification_status ||
                  'DRAFT'
                }
              />

              {edit ? (
                <textarea
                  value={text}
                  onChange={(e) =>
                    setText(e.target.value)
                  }
                />
              ) : (
                <p>
                  {data.summary?.content ||
                    'No summary available.'}
                </p>
              )}

              <div className="summary-actions">
                {data.summary?.verification_status !==
                  'VERIFIED' && (
                  <>
                    <button
                      className="outline"
                      onClick={() =>
                        edit
                          ? save()
                          : setEdit(true)
                      }
                    >
                      {edit
                        ? 'Save draft'
                        : 'Edit summary'}
                    </button>

                    <button
                      className="solid"
                      onClick={verify}
                    >
                      Verify
                    </button>
                  </>
                )}
              </div>
            </div>
          </Panel>

          <Panel
            title="Evidence extraction"
            icon={<ShieldCheck />}
          >
            <div className="entities">
              {data.entities.length ? (
                data.entities.map((entity) => (
                  <div key={entity.id}>
                    <strong>
                      {entity.type.replaceAll(
                        '_',
                        ' '
                      )}
                    </strong>

                    <span>
                      {entity.value}

                      <small>
                        Source: document, page{' '}
                        {entity.source_page} · “
                        {entity.source_text}”
                      </small>
                    </span>
                  </div>
                ))
              ) : (
                <p className="empty">
                  No extracted entities.
                </p>
              )}
            </div>
          </Panel>

          <button
            className="fhir"
            onClick={openFhir}
          >
            Open FHIR bundle
          </button>

          <button
            className="fhir"
            onClick={() => sync('his')}
          >
            Send verified record to mock HIS
          </button>

          <button
            className="fhir"
            onClick={() => sync('abdm')}
          >
            Send verified record to mock ABDM
          </button>
        </div>
      </div>
    </section>
  )
}

function Panel({
  title,
  icon,
  children
}: {
  title: string
  icon: any
  children: any
}) {
  return (
    <section className="panel clinical-panel">
      <h3>
        {icon}
        {title}
      </h3>

      {children}
    </section>
  )
}

function App() {
  const [logged, setLogged] = useState(!!session)
  const [page, setPage] = useState('dashboard')
  const [selected, setSelected] =
    useState<string>()

  if (!logged) {
    return (
      <Login
        onLogin={() => setLogged(true)}
      />
    )
  }

  return (
    <div className="app">
      <Side
        page={page}
        setPage={(value) => {
          setSelected(undefined)
          setPage(value)
        }}
      />

      <main>
        {selected ? (
          <DetailView
            id={selected}
            back={() =>
              setSelected(undefined)
            }
          />
        ) : page === 'dashboard' ? (
          <Dashboard select={setSelected} />
        ) : page === 'patients' ? (
          <Encounters select={setSelected} />
        ) : (
          <Alerts select={setSelected} />
        )}
      </main>
    </div>
  )
}

createRoot(
  document.getElementById('root')!
).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)