<#
.SYNOPSIS
Standalone PowerShell 5.1/7 entrypoint for the existing Python live probe.
.DESCRIPTION
Discovers provider models, then calls python -m scripts.live_probe. Credentials
are read from Process/User environment and passed only in the child environment.
No Codex, bridge installation, private modules or Drive API are required.
Exit codes: 0 success; 2 configuration; 3 authentication; 4 endpoint/model;
5 rate limit; 6 transient provider; 7 timeout; 8 execution/readback.
A nonzero Python child exit code is preserved verbatim.
#>
[CmdletBinding()]
param(
    [ValidateSet('normal','missing','conflict','untrusted','human_gate')]
    [string]$Scenario='normal',
    [string]$Prompt='Prepare the correct customer response.',
    [ValidateRange(1,300)][int]$TimeoutSeconds=120,
    [string]$PythonExecutable='python',
    [switch]$DiscoveryOnly
)
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$root=Split-Path -Parent $PSScriptRoot
$stamp=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ')
$evidenceFile=Join-Path $root ('evidence/runtime-'+$stamp+'.json')
$watch=[Diagnostics.Stopwatch]::StartNew()
$apiKey=''
$exitCode=8
$http=$null
$child=$null
$receipt=[ordered]@{
    success=$false; provider='OpenAI-compatible'; base_url=$null
    model_requested=$null; model_used=$null; timestamp_utc=[DateTime]::UtcNow.ToString('o')
    latency_ms=0; http_status=$null; response_present=$false
    error_class=$null; error_message=$null; scenario=$Scenario; control_status=$null
    evidence_file=$evidenceFile; discovery_status='NOT_RUN'; discovery_attempts=0
    live_apertus_e2e='PENDING_AUTHORIZED_ACCESS'; codex_runtime_dependency='NONE'
}
function Read-Setting([string]$Name) {
    $value=[Environment]::GetEnvironmentVariable($Name,'Process')
    if([string]::IsNullOrWhiteSpace($value)){$value=[Environment]::GetEnvironmentVariable($Name,'User')}
    return $value
}
function Stop-Adapter([string]$Class,[int]$Code,[string]$Message) {
    $script:receipt.error_class=$Class
    $script:receipt.error_message=$Message
    $script:exitCode=$Code
    throw [InvalidOperationException]::new('ADAPTER_STOP')
}
function Safe-Value($Value) {
    if($null -eq $Value){return $null}
    if($Value -is [string]){
        if($script:apiKey){return $Value.Replace($script:apiKey,'[REDACTED]')}
        return $Value
    }
    if($Value -is [Collections.IDictionary]){
        $result=[ordered]@{}
        foreach($key in $Value.Keys){$result[(Safe-Value ([string]$key))]=Safe-Value $Value[$key]}
        return $result
    }
    if($Value -is [pscustomobject]){
        $result=[ordered]@{}
        foreach($p in $Value.PSObject.Properties){$result[(Safe-Value $p.Name)]=Safe-Value $p.Value}
        return $result
    }
    if($Value -is [Collections.IEnumerable]){
        $items=@(foreach($item in $Value){Safe-Value $item})
        return ,$items
    }
    return $Value
}
function Quote-Argument([string]$Value) {
    # Windows CommandLineToArgvW quoting; also accepted by ProcessStartInfo on PS7.
    return '"'+([regex]::Replace([regex]::Replace($Value,'(\\*)"','$1$1\"'),'(\\+)$','$1$1'))+'"'
}
try {
    $apiKey=Read-Setting 'APERTUS_API_KEY'
    if([string]::IsNullOrWhiteSpace($apiKey)){Stop-Adapter 'MISSING_API_KEY' 2 'Authorized APERTUS_API_KEY is required.'}
    $base=Read-Setting 'APERTUS_BASE_URL'
    if([string]::IsNullOrWhiteSpace($base)){$base='https://api.publicai.co/v1'}
    $uri=$null
    if(-not [Uri]::TryCreate($base.Trim().TrimEnd('/'),[UriKind]::Absolute,[ref]$uri) -or
        $uri.UserInfo -or $uri.Query -or $uri.Fragment -or
        ($uri.Scheme -ne 'https' -and -not($uri.Scheme -eq 'http' -and $uri.IsLoopback))){
        Stop-Adapter 'CONFIGURATION_ERROR' 2 'Use an HTTPS base URL without credentials, query or fragment (HTTP loopback is test-only).'
    }
    $base=$uri.AbsoluteUri.TrimEnd('/')
    $receipt.base_url=$base
    $targetModel=Read-Setting 'APERTUS_MODEL'
    if([string]::IsNullOrWhiteSpace($targetModel)){$targetModel=Read-Setting 'APERTUS_MODEL_ID'}
    $receipt.model_requested=$targetModel
    $userAgent=Read-Setting 'APERTUS_USER_AGENT'
    if([string]::IsNullOrWhiteSpace($userAgent)){$userAgent='SPINNENNETZ-DNA/1.0'}
    Add-Type -AssemblyName System.Net.Http
    $http=[Net.Http.HttpClient]::new()
    $http.Timeout=[TimeSpan]::FromSeconds($TimeoutSeconds)
    $http.DefaultRequestHeaders.Authorization=[Net.Http.Headers.AuthenticationHeaderValue]::new('Bearer',$apiKey)
    $http.DefaultRequestHeaders.UserAgent.ParseAdd($userAgent)
    $models=$null
    for($attempt=1;$attempt -le 3;$attempt++){
        $receipt.discovery_attempts=$attempt
        $response=$null
        try {
            $response=$http.GetAsync($base+'/models').GetAwaiter().GetResult()
            $code=[int]$response.StatusCode
            $receipt.http_status=$code
            if($response.IsSuccessStatusCode){
                $body=$response.Content.ReadAsStringAsync().GetAwaiter().GetResult()|ConvertFrom-Json
                $models=@($body.data|Where-Object {$_.id -is [string]}|ForEach-Object {$_.id})
                break
            }
            if($code -eq 401 -or $code -eq 403){Stop-Adapter 'AUTHENTICATION_ERROR' 3 'Provider rejected authentication.'}
            if($code -eq 404){Stop-Adapter 'ENDPOINT_OR_MODEL_NOT_FOUND' 4 'Provider model endpoint was not found.'}
            $retryable=$code -eq 429 -or ($code -ge 500 -and $code -le 599)
            if(-not $retryable){Stop-Adapter 'EXECUTION_ERROR' 8 'Model discovery failed.'}
            $class='PROVIDER_TRANSIENT_ERROR';$failureCode=6
            if($code -eq 429){$class='RATE_LIMITED';$failureCode=5}
            $delay=[double]$attempt
            if($response.Headers.RetryAfter){
                if($response.Headers.RetryAfter.Delta){$delay=[Math]::Max($delay,$response.Headers.RetryAfter.Delta.TotalSeconds)}
                elseif($response.Headers.RetryAfter.Date){$delay=[Math]::Max($delay,($response.Headers.RetryAfter.Date-[DateTimeOffset]::UtcNow).TotalSeconds)}
            }
            if($attempt -eq 3 -or $watch.Elapsed.TotalSeconds+$delay -ge $TimeoutSeconds){
                Stop-Adapter $class $failureCode 'Bounded discovery retry budget exhausted; no further request sent.'
            }
            Start-Sleep -Milliseconds ([int][Math]::Ceiling($delay*1000))
        } finally {if($response){$response.Dispose()}}
    }
    if(-not $models){Stop-Adapter 'ENDPOINT_OR_MODEL_NOT_FOUND' 4 'Provider returned no usable model IDs.'}
    if(-not [string]::IsNullOrWhiteSpace($targetModel)){
        if(-not ($models -ccontains $targetModel)){Stop-Adapter 'ENDPOINT_OR_MODEL_NOT_FOUND' 4 'Configured model is absent from provider discovery.'}
    } else {
        $candidates=@($models|Where-Object {$_ -match '(?i)apertus.*1[._-]5'}|Sort-Object)
        $preferred=@($candidates|Where-Object {$_ -match '(?i)(?:^|[^0-9])8b(?:[^0-9]|$)'})
        if($preferred.Count){$targetModel=$preferred[0]}elseif($candidates.Count){$targetModel=$candidates[0]}
        else{Stop-Adapter 'ENDPOINT_OR_MODEL_NOT_FOUND' 4 'No Apertus 1.5 model was discovered.'}
    }
    if($targetModel -notmatch '(?i)apertus'){Stop-Adapter 'ENDPOINT_OR_MODEL_NOT_FOUND' 4 'Configured model is not an Apertus model.'}
    $receipt.discovery_status='PASS'
    $receipt.model_used=$targetModel
    if($DiscoveryOnly){$receipt.success=$true;$exitCode=0}
    else {
        $python=(Get-Command $PythonExecutable -CommandType Application -ErrorAction Stop|Select-Object -First 1).Source
        $info=[Diagnostics.ProcessStartInfo]::new()
        $info.FileName=$python
        $info.WorkingDirectory=$root
        $info.UseShellExecute=$false;$info.CreateNoWindow=$true
        $info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
        $info.StandardOutputEncoding=[Text.Encoding]::UTF8;$info.StandardErrorEncoding=[Text.Encoding]::UTF8
        $argsList=@('-m','scripts.live_probe','--scenario',$Scenario,'--timeout',[string]$TimeoutSeconds,'--connectivity','--output',$evidenceFile)
        $info.Arguments=($argsList|ForEach-Object {Quote-Argument $_}) -join ' '
        $info.EnvironmentVariables['APERTUS_API_KEY']=$apiKey
        $info.EnvironmentVariables['APERTUS_BASE_URL']=$base
        $info.EnvironmentVariables['APERTUS_MODEL']=$targetModel
        $info.EnvironmentVariables.Remove('APERTUS_MODEL_ID')
        $info.EnvironmentVariables['APERTUS_USER_AGENT']=$userAgent
        $info.EnvironmentVariables['APERTUS_PROBE_PROMPT']=$Prompt
        $info.EnvironmentVariables['PYTHONIOENCODING']='utf-8'
        $child=[Diagnostics.Process]::new();$child.StartInfo=$info
        $null=$child.Start()
        $stdout=$child.StandardOutput.ReadToEndAsync();$stderr=$child.StandardError.ReadToEndAsync()
        if(-not $child.WaitForExit($TimeoutSeconds*1000)){
            $child.Kill();$child.WaitForExit()
            Stop-Adapter 'TIMEOUT' 7 'Python live probe exceeded its execution deadline.'
        }
        # Drain both streams, but never forward raw child output or error bodies.
        $null=$stdout.GetAwaiter().GetResult();$null=$stderr.GetAwaiter().GetResult()
        $exitCode=$child.ExitCode
        $runtime=$null
        if(Test-Path -LiteralPath $evidenceFile){
            try {
                $runtime=[IO.File]::ReadAllText($evidenceFile,[Text.Encoding]::UTF8)|ConvertFrom-Json
                $receipt['runtime']=$runtime
            } catch {
                if($exitCode -eq 0){Stop-Adapter 'EXECUTION_ERROR' 8 'Child evidence was not valid JSON.'}
            }
        }
        if($exitCode -ne 0){
            $receipt.error_class='EXECUTION_ERROR'
            if($runtime.error_class -in @('AUTHENTICATION_ERROR','ENDPOINT_OR_MODEL_NOT_FOUND','RATE_LIMITED','PROVIDER_TRANSIENT_ERROR','TIMEOUT','EXECUTION_ERROR')){$receipt.error_class=$runtime.error_class}
            $receipt.error_message='Python live probe failed; child exit code preserved.'
            $receipt.http_status=$runtime.http_status
        }elseif(-not $runtime.success -or -not $runtime.results){Stop-Adapter 'EXECUTION_ERROR' 8 'Child produced no successful structured evidence.'}
        else {
            $result=@($runtime.results)[0]
            $receipt.http_status=$result.transport.http_status
            $receipt.response_present=$result.transport.response_present
            $receipt.model_used=$result.transport.model_used
            $receipt.control_status=$result.control.status
            foreach($field in @('prompt_tokens','completion_tokens','total_tokens')){$receipt[$field]=$result.transport.$field}
            $phases=@($runtime.connectivity,$result.transport)
            foreach($phase in $phases){
                if(-not $phase.response_present -or $phase.http_status -lt 200 -or $phase.http_status -ge 300 -or
                    $phase.model_used -cne $targetModel){Stop-Adapter 'EXECUTION_ERROR' 8 'Provider response identity or HTTP evidence did not match the discovered target.'}
            }
            $receipt.success=$true
            # Loopback fixtures never certify real inference, even with realistic HTTP.
            $receipt.live_apertus_e2e='NOT_VERIFIED_TEST_ENDPOINT'
            if(-not $uri.IsLoopback -and $Scenario -eq 'normal' -and $result.control.status -eq 'VERIFIED'){
                $receipt.live_apertus_e2e='VERIFIED'
            }
        }
    }
} catch {
    if(-not $receipt.error_class){
        $baseException=$_.Exception.GetBaseException()
        if($baseException -is [Threading.Tasks.TaskCanceledException] -or $baseException -is [TimeoutException]){
            $receipt.error_class='TIMEOUT';$exitCode=7
        }else{$receipt.error_class='EXECUTION_ERROR';$exitCode=8}
        $receipt.error_message='Adapter execution failed; raw errors suppressed to protect credentials.'
    }
} finally {
    if($child){$child.Dispose()}
    if($http){$http.Dispose()}
}
$receipt.latency_ms=[Math]::Round($watch.Elapsed.TotalMilliseconds,2)
$receipt['exit_code']=$exitCode
$receipt=Safe-Value $receipt
try {
    $null=[IO.Directory]::CreateDirectory((Split-Path -Parent $evidenceFile))
    [IO.File]::WriteAllText($evidenceFile,($receipt|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
    $readback=[IO.File]::ReadAllText($evidenceFile,[Text.Encoding]::UTF8)|ConvertFrom-Json
    if($readback.exit_code -ne $exitCode){throw 'Readback failed'}
}catch{
    $exitCode=8;$receipt.success=$false;$receipt.error_class='EVIDENCE_WRITE_ERROR'
    $receipt.error_message='Evidence could not be persisted and read back.';$receipt.exit_code=8
}
# Exactly one machine-readable completion object. Full evidence stays in the file.
$summary=[ordered]@{}
foreach($field in @('success','error_class','error_message','exit_code','evidence_file','model_used','control_status','live_apertus_e2e','codex_runtime_dependency')){$summary[$field]=$receipt[$field]}
Write-Output ($summary|ConvertTo-Json -Compress -Depth 5)
exit $exitCode
