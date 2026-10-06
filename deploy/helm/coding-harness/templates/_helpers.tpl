{{- define "ch.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "ch.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "ch.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "ch.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/* Usage: include "ch.selectorLabels" (dict "ctx" . "component" "api") */}}
{{- define "ch.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ch.name" .ctx }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{/* Usage: include "ch.image" (dict "ctx" . "image" .Values.api.image) */}}
{{- define "ch.image" -}}
{{- $tag := .image.tag | default .ctx.Chart.AppVersion -}}
{{- if .ctx.Values.global.imageRegistry -}}
{{- printf "%s/%s:%s" .ctx.Values.global.imageRegistry .image.repository $tag -}}
{{- else -}}
{{- printf "%s:%s" .image.repository $tag -}}
{{- end -}}
{{- end }}

{{- define "ch.secretName" -}}
{{- .Values.secrets.existingSecret | default (printf "%s-secrets" (include "ch.fullname" .)) }}
{{- end }}

{{- define "ch.postgresql.fullname" -}}
{{- printf "%s-postgresql" (include "ch.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "ch.corsOrigins" -}}
{{- if .Values.api.corsOrigins }}
{{- .Values.api.corsOrigins }}
{{- else if and .Values.ingress.enabled .Values.ingress.hosts }}
{{- printf "%s://%s" (ternary "https" "http" (gt (len .Values.ingress.tls) 0)) (first .Values.ingress.hosts) }}
{{- else }}
{{- "*" }}
{{- end }}
{{- end }}

{{- define "ch.imagePullSecrets" -}}
{{- with .Values.global.imagePullSecrets }}
imagePullSecrets:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- end }}
