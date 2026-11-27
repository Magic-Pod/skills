一括実行 {{batch_run_link}} で失敗しました。

* テスト実行: {{test_run_link}}
{{#pattern}}
* 実行パターン: {{pattern}}
{{/pattern}}
{{#data_pattern_number}}
* データパターン: {{data_pattern_number}}
{{/data_pattern_number}}
{{#started_at}}
* 実行日時: {{started_at}}
{{/started_at}}
{{#data_pattern_values}}

### データパターンの値
```
{{data_pattern_values}}
```
{{/data_pattern_values}}
{{#failed_step}}

### 失敗ステップ
```
{{failed_step}}
```
{{/failed_step}}
{{#error_message}}

### エラーメッセージ
```
{{error_message}}
```
{{/error_message}}
