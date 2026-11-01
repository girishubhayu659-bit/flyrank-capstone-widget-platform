(function() {
    'use strict';

    // 1. Identify current script and widget id
    var currentScript = document.currentScript;
    if (!currentScript) {
        var scripts = document.getElementsByTagName('script');
        currentScript = scripts[scripts.length - 1];
    }

    var scriptSrc = currentScript ? currentScript.src : '';
    var urlParams = new URLSearchParams(scriptSrc.split('?')[1] || '');
    var widgetId = urlParams.get('id');

    if (!widgetId) {
        console.error('[FlyRank Widget] Missing widget id parameter in script src.');
        return;
    }

    var baseUrl = scriptSrc.substring(0, scriptSrc.indexOf('/widget.js'));
    if (!baseUrl) {
        baseUrl = 'http://localhost:8000';
    }

    // 2. Fetch widget config
    var configUrl = baseUrl + '/widgets/' + encodeURIComponent(widgetId) + '/config';

    fetch(configUrl)
        .then(function(res) {
            if (!res.ok) {
                throw new Error('Failed to load widget configuration (' + res.status + ')');
            }
            return res.json();
        })
        .then(function(config) {
            renderWidget(config, baseUrl);
        })
        .catch(function(err) {
            console.error('[FlyRank Widget] Error:', err);
        });

    // 3. Render widget into page DOM
    function renderWidget(config, apiBase) {
        var containerId = 'flyrank-widget-' + config.id;
        if (document.getElementById(containerId)) return;

        var hostDiv = document.createElement('div');
        hostDiv.id = containerId;
        hostDiv.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:999999;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;box-shadow:0 10px 25px -5px rgba(0,0,0,0.1),0 8px 10px -6px rgba(0,0,0,0.1);border-radius:12px;background:#ffffff;border:1px solid #e2e8f0;width:340px;overflow:hidden;transition:all 0.3s ease;';

        var primaryColor = (config.display_options && config.display_options.primary_color) || '#2563eb';

        var html = '<div style="background:' + primaryColor + ';color:#ffffff;padding:16px 20px;">' +
            '<h3 style="margin:0;font-size:16px;font-weight:600;">' + escapeHtml(config.title) + '</h3>' +
            (config.description ? '<p style="margin:4px 0 0 0;font-size:13px;opacity:0.9;">' + escapeHtml(config.description) + '</p>' : '') +
            '</div>' +
            '<form id="' + containerId + '-form" style="padding:20px;display:flex;flex-direction:column;gap:12px;">';

        // Add form fields
        var fields = config.form_fields || [];
        for (var i = 0; i < fields.length; i++) {
            var f = fields[i];
            var fName = escapeHtml(f.name);
            var fLabel = escapeHtml(f.label);
            var fType = escapeHtml(f.type || 'text');
            var fReq = f.required ? 'required' : '';

            html += '<div>' +
                '<label style="display:block;font-size:12px;font-weight:600;color:#475569;margin-bottom:4px;">' + fLabel + (f.required ? ' *' : '') + '</label>';

            if (f.type === 'textarea') {
                html += '<textarea name="' + fName + '" ' + fReq + ' style="width:100%;box-sizing:border-box;padding:8px 10px;border:1px solid #cbd5e1;border-radius:6px;font-size:13px;resize:vertical;min-height:60px;"></textarea>';
            } else {
                html += '<input type="' + fType + '" name="' + fName + '" ' + fReq + ' style="width:100%;box-sizing:border-box;padding:8px 10px;border:1px solid #cbd5e1;border-radius:6px;font-size:13px;">';
            }
            html += '</div>';
        }

        // Invisible Honeypot Field (Bot Trap)
        html += '<input type="text" name="hp_field" style="display:none !important;visibility:hidden;position:absolute;left:-9999px;" tabindex="-1" autocomplete="off">';

        // Submit Button & Status Banner
        html += '<div id="' + containerId + '-status" style="display:none;font-size:12px;padding:8px;border-radius:6px;text-align:center;"></div>';
        html += '<button type="submit" id="' + containerId + '-btn" style="background:' + primaryColor + ';color:#ffffff;border:none;padding:10px 16px;border-radius:6px;font-size:14px;font-weight:600;cursor:pointer;transition:opacity 0.2s;">' + escapeHtml(config.button_text || 'Submit') + '</button>';
        html += '</form>';

        hostDiv.innerHTML = html;
        document.body.appendChild(hostDiv);

        // Bind form submission
        var form = document.getElementById(containerId + '-form');
        var statusDiv = document.getElementById(containerId + '-status');
        var btn = document.getElementById(containerId + '-btn');

        form.addEventListener('submit', function(e) {
            e.preventDefault();
            btn.disabled = true;
            btn.innerText = 'Submitting...';
            statusDiv.style.display = 'none';

            var formData = new FormData(form);
            var dataObj = {};
            var hpFieldVal = '';

            formData.forEach(function(value, key) {
                if (key === 'hp_field') {
                    hpFieldVal = value;
                } else {
                    dataObj[key] = value;
                }
            });

            var payload = {
                widget_id: config.id,
                data: dataObj,
                hp_field: hpFieldVal
            };

            fetch(config.submit_url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            })
            .then(function(res) {
                return res.json().then(function(json) {
                    return { ok: res.ok, status: res.status, body: json };
                });
            })
            .then(function(result) {
                btn.disabled = false;
                btn.innerText = config.button_text || 'Submit';

                if (result.ok && result.body.success) {
                    statusDiv.style.display = 'block';
                    statusDiv.style.background = '#dcfce7';
                    statusDiv.style.color = '#15803d';
                    statusDiv.innerText = 'Thank you! Your submission has been received.';
                    form.reset();
                    setTimeout(function() {
                        statusDiv.style.display = 'none';
                    }, 5000);
                } else {
                    statusDiv.style.display = 'block';
                    statusDiv.style.background = '#fee2e2';
                    statusDiv.style.color = '#b91c1c';
                    statusDiv.innerText = result.body.detail || result.body.message || 'Submission failed. Please check inputs.';
                }
            })
            .catch(function(err) {
                btn.disabled = false;
                btn.innerText = config.button_text || 'Submit';
                statusDiv.style.display = 'block';
                statusDiv.style.background = '#fee2e2';
                statusDiv.style.color = '#b91c1c';
                statusDiv.innerText = 'Network error. Please try again.';
            });
        });
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
})();
